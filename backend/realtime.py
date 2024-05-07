import asyncio
import logging
import queue
import threading
import os
import requests
import pyaudio
from google.cloud import speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment
from pydub.playback import play
import io
import json
import webrtcvad

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

input_language = 'ko-KR'
output_language = 'en'

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccount.json'

    @staticmethod
    def load_config():
        try:
            with open('config.json', 'r') as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            logging.error("Config file not found.")
            exit(1)

config_manager = ConfigManager()

speech_client = speech.SpeechClient()
translate_client = translate.Client()

RATE = 16000
CHUNK = int(RATE / 10)

class MicrophoneStream:
    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self.vad = webrtcvad.Vad(3)

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    async def generator(self):
        frame_duration = 0.02
        frame_size = int(self._rate * frame_duration)
        buffer = b''
        while not self.closed:
            data = await asyncio.get_event_loop().run_in_executor(None, self._buff.get)
            if data is None:
                return
            buffer += data
            while len(buffer) >= frame_size:
                frame = buffer[:frame_size]
                buffer = buffer[frame_size:]
                yield frame

def translate_text(text, target_language=output_language):
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        logging.error(f"Error during translation: {e}")
        raise

def text_to_speech_rest_api(voice_id, text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": config_manager.config['elevenLabsAPIKey']
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "similarity_boost": 0.5,
            "stability": 0.5,
            "style": 0.5,
            "use_speaker_boost": True
    }
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        output_file = "output.mp3"
        with open(output_file, 'wb') as f:
            f.write(response.content)
        logging.info(f"Audio saved to {output_file}")
        play(AudioSegment.from_file(output_file, format="mp3"))
    else:
        logging.error(f"Error from Eleven Labs API: {response.status_code} - {response.text}")

class AudioStreamBridge:
    def __init__(self, audio_generator):
        self.audio_generator = audio_generator
        self.buffer = queue.Queue()

    def stream_audio_to_buffer(self):
        asyncio.run(self._stream_audio())

    async def _stream_audio(self):
        async for chunk in self.audio_generator:
            self.buffer.put(chunk)

    def generator(self):
        while True:
            chunk = self.buffer.get()
            if chunk is None:
                break
            yield chunk

def google_speech_to_text_stream(bridge, language_code=input_language):
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
        enable_automatic_punctuation=True
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    requests = (speech.StreamingRecognizeRequest(audio_content=chunk) for chunk in bridge.generator())
    responses = client.streaming_recognize(streaming_config, requests)

    try:
        for response in responses:
            for result in response.results:
                if result.is_final:
                    yield result.alternatives[0].transcript
    except Exception as e:
        logging.error(f"Error processing stream: {e}")

async def main():
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        bridge = AudioStreamBridge(audio_generator)
        thread = threading.Thread(target=bridge.stream_audio_to_buffer, daemon=True)
        thread.start()

        for transcript in google_speech_to_text_stream(bridge):
            if transcript:
                print(f"Transcript: {transcript}")
                translated_text = translate_text(transcript, target_language='ko')
                print(f"Translated: {translated_text}")
                text_to_speech_rest_api(config_manager.config['voiceId'], translated_text)

        bridge.buffer.put(None)
        thread.join()

if __name__ == "__main__":
    asyncio.run(main())

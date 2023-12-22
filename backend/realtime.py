import asyncio
import logging
import queue
import json
import os
import requests
import pyaudio
from google.cloud import speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment
from pydub.playback import play
import webrtcvad
import io

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

# Load configuration from 'config.json'
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
    eleven_labs_api_key = config['elevenLabsAPIKey']
    voice_id = config['voiceId']

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccount.json'

# Load Google Cloud clients
speech_client = speech.SpeechClient()
translate_client = translate.Client()

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""
    def __init__(self, rate=RATE, chunk=CHUNK):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self.closed = True
        self.vad = webrtcvad.Vad(1)

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
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    async def generator(self):
        """Asynchronous generator that yields audio chunks."""
        frame_duration = 0.02  # Frame duration in seconds (e.g., 0.02 for 20 ms)
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

async def transcribe_stream(audio_generator, vad):
    logging.info("Starting transcription.")
    audio_chunks = []
    current_speech = b""
    in_speech = False
    async for frame in audio_generator:
        if vad.is_speech(frame, RATE):
            if not in_speech:
                in_speech = True
            current_speech += frame
        elif in_speech:
            in_speech = False
            audio_chunks.append(current_speech)
            current_speech = b""

        if not in_speech and audio_chunks:
            audio_data = b''.join(audio_chunks)
            audio_chunks = []
            yield audio_data

def translate_text(text, target_language='ko'):
    logging.info(f"Translating text to {target_language}.")
    try:
        result = translate_client.translate(text, target_language=target_language)
        translated_text = result['translatedText']
        return translated_text
    except Exception as e:
        logging.error(f"Error during translation: {e}")
        raise

def text_to_speech_rest_api(voice_id, text):
    """Sends text to Eleven Labs REST API for TTS and plays back the audio."""
    logging.info("Sending text to Eleven Labs REST API for TTS.")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {
        "xi-api-key": eleven_labs_api_key,
        "Content-Type": "application/json"
    }

    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "similarity_boost": 0.8,
            "stability": 0.8
        }
    }

    response = requests.post(url, headers=headers, json=body, stream=True)

    if response.status_code == 200:
        audio_data = response.content
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        play(audio_segment)
    else:
        logging.error(f"Error from Eleven Labs API: {response.status_code} - {response.text}")

def process_transcript(transcript):
    if "exit" in transcript or "quit" in transcript:
        logging.info("Exiting program.")
        exit()
    if transcript.strip():
        translated_text = translate_text(transcript.strip())    
        logging.info(f"Translation: {translated_text}")
        text_to_speech_rest_api(voice_id, translated_text)

async def main():
    with MicrophoneStream(RATE, CHUNK) as stream:
        vad = webrtcvad.Vad(1)
        audio_generator = stream.generator()
        async for audio_data in transcribe_stream(audio_generator, vad):
            audio_segment = AudioSegment.from_raw(io.BytesIO(audio_data), sample_width=2, frame_rate=RATE, channels=1)
            # Transcribe the audio segment using Google Speech-to-Text API
            response = speech_client.recognize(
                audio=speech.RecognitionAudio(content=audio_data),
                config=speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=RATE,
                    language_code='en-US',
                ),
            )
            for result in response.results:
                transcript = result.alternatives[0].transcript
                logging.info(f"Transcript: {transcript}")
                process_transcript(transcript)

if __name__ == "__main__":
    asyncio.run(main())

import os
import requests
from google.cloud import speech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment
import json

#  get apiKey from config.json
with open('config.json') as json_file:
    data = json.load(json_file)
    api_key = data['elevenLabsAPIKey']
    voice_id = data['voiceId']
    translate_from = data['translateFrom']
    translate_to = data['translateTo']
    input_audio_path = data['inputAudioPath']

# Set the path to your Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccount.json'


def transcribe_audio(speech_file, lang=translate_from):
    """Transcribe the given audio file using Google Cloud Speech."""
    client = speech.SpeechClient()

    with open(speech_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,  # Adjusted to match the WAV file's sample rate
        language_code=lang,
    )

    response = client.recognize(config=config, audio=audio)

    # Just take the first result here for simplicity
    for result in response.results:
        return result.alternatives[0].transcript

def translate_text(text, target_language=translate_to):
    """Translate the given text to the target language using Google Cloud Translation."""
    translate_client = translate.Client()

    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

def convert_audio(audio_path):
    """Converts the given audio file to WAV format."""
    audio_format = audio_path.split('.')[-1]
    output_path = "converted_audio.wav"

    if audio_format == "mp3":
        audio_segment = AudioSegment.from_mp3(audio_path)
    elif audio_format == "m4a":
        audio_segment = AudioSegment.from_file(audio_path, "m4a")
    else:
        raise ValueError(f"Unsupported audio format: {audio_format}")

    audio_segment.export(output_path, format="wav")
    return output_path

def generate_voice_file(text, voice_id, api_key, output_file="output_voice.mp3"):
    """Generate a voice file using Eleven Labs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = {
        "model_id": "eleven_monolingual_v1",  # Adjusted as per documentation
        "text": text,
        "voice_settings": {
            # Adjust these settings as needed
            "similarity_boost": 0.75,
            "stability": 0.50
        }
    }
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key  # Updated as per documentation
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        CHUNK_SIZE = 1024
        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    file.write(chunk)
        print(f"Voice file saved as {output_file}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Convert audio to WAV format
converted_audio = convert_audio(input_audio_path)

# Transcribe and translate
transcribed_text = transcribe_audio(converted_audio)
translated_text = translate_text(transcribed_text, translate_to)  # Translate to english

# Generate voice file using Eleven Labs API
generate_voice_file(translated_text, voice_id, api_key, "translated_voice.mp3")

print(f"Original Text: {transcribed_text}")
print(f"Translated Text: {translated_text}")
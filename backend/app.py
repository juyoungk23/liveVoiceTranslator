from flask import Flask, request, jsonify, send_file
import os
import requests
from flask_cors import CORS
from pydub.utils import mediainfo
from pydub import AudioSegment 
import logging
from logging.handlers import RotatingFileHandler
from pydub.exceptions import CouldntDecodeError
from google.cloud import secretmanager
from google.oauth2 import service_account
from google.cloud import speech
from google.cloud import translate_v3 as translate
import json
import time
import openai

app = Flask(__name__)
CORS(app)  # This enables CORS for all routes

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('development.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error including the stack trace
    app.logger.error(f"Unhandled Exception: {e}", exc_info=True)
    return jsonify({"error": "An internal server error occurred"}), 500


def get_secret(project_id, secret_id):
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode('UTF-8')
# Retrieve API keys from Google Cloud Secret Manager
project_id = "70513175587"
openai_api_key = get_secret(project_id, "OpenAIAPIKey")
elevenlabs_api_key = get_secret(project_id, "ElevenLabsAPIKey")
openai_client = openai.OpenAI(api_key=openai_api_key)

def get_credentials():
    # ID of your project and the ID of the secret you want to access
    cloud_translation_service_account_secret_id = "cloud-translation-service-account"

    # access OpenAIAPIKey and ElevenLabsAPIKey secrets

    # Build the client and request object
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{cloud_translation_service_account_secret_id}/versions/latest"
   
    response = client.access_secret_version(request={"name": name})

    # Load credentials from the secret payload
    credentials_info = json.loads(response.payload.data.decode('UTF-8'))
    credentials = service_account.Credentials.from_service_account_info(credentials_info)

    return credentials


def create_speech_client():
    credentials = get_credentials()
    client = speech.SpeechClient(credentials=credentials)
    return client

def create_translate_client():
    credentials = get_credentials()
    client = translate.TranslationServiceClient(credentials=credentials)
    return client

# Load configuration from JSON file
with open('config.json') as json_file:
    data = json.load(json_file)
    voices = data['voices']
    translate_from = data['translateFrom']
    translate_to = data['translateTo']

def transcribe_audio(speech_file):
    try:
        with open(speech_file, 'rb') as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.get('text')
    except Exception as e:
        app.logger.error(f"Error in transcribing audio: {e}", exc_info=True)
        return None


def transcribe_audio_google(speech_file, lang):
    client = create_speech_client() 

    try:
        audio_info = mediainfo(speech_file)
        audio_format = audio_info.get('format_name', '').split(',')[0].lower()
        sample_rate = int(audio_info.get('sample_rate', '16000'))
    except Exception as e:
        app.logger.error(f"Error in getting audio file info: {e}", exc_info=True)
        sample_rate = 16000
        audio_format = 'unknown'

    try:
        if audio_format in ['matroska', 'webm', 'mov']:
            speech_file = convert_audio_to_wav(speech_file)
            if speech_file is None:
                return None
            audio_format = 'wav'
    except Exception as e:
        app.logger.error(f"Error in converting audio file: {e}", exc_info=True)
        return None

    try:
        if audio_format in ['wav', 'wave'] and audio_info.get('bits_per_sample', '16') != '16':
            speech_file = convert_audio_to_16_bit(speech_file)
            if speech_file is None:
                return None
        if audio_format == 'mp3':
            encoding = speech.RecognitionConfig.AudioEncoding.MP3
        elif audio_format in ['wav', 'wave']:
            encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16
        else:
            app.logger.error(f"Unsupported audio format: {audio_format}")
            return None
    except Exception as e:
        app.logger.error(f"Error in handling audio encoding: {e}", exc_info=True)
        return None

    try:
        with open(speech_file, 'rb') as audio_file:
            content = audio_file.read()
    except Exception as e:
        app.logger.error(f"Error in reading audio file: {e}", exc_info=True)
        return None

    try:
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sample_rate,
            language_code=lang,
        )
    except Exception as e:
        app.logger.error(f"Error in setting up recognition config: {e}", exc_info=True)
        return None

    try:
        response = client.recognize(config=config, audio=audio)
        if not response.results:
            app.logger.error("No transcription results returned from Google Speech-to-Text API")
            return "No text was given"
        return response.results[0].alternatives[0].transcript
    except Exception as e:
        app.logger.error(f"Error in transcribing audio: {e}", exc_info=True)
        return None


def convert_audio_to_16_bit(input_file):
    output_file = os.path.splitext(input_file)[0] + '_16bit.wav'

    try:
        audio = AudioSegment.from_file(input_file)
        audio = audio.set_sample_width(2)
        audio.export(output_file, format='wav')
    except CouldntDecodeError as e:
        app.logger.error(f"Could not decode the input file: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Error in converting audio file to 16-bit: {e}", exc_info=True)
        return None

    return output_file

def convert_audio_to_wav(input_file):
    """Converts an audio file to WAV format with 16-bit samples and trims it to 30 seconds."""
    output_file = os.path.splitext(input_file)[0] + '.wav'

    try:
        # Load the input file with pydub, which automatically extracts the audio
        audio = AudioSegment.from_file(input_file)

        # Ensure the audio is 16-bit, mono, and at the desired frame rate
        audio = audio.set_sample_width(2)  # 2 bytes (16 bits)
        audio = audio.set_frame_rate(16000)  # 16 kHz
        audio = audio.set_channels(1)  # Mono
        audio.export(output_file, format='wav')
    except CouldntDecodeError as e:
        app.logger.error(f"Could not decode the input file: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Error in converting audio file: {e}", exc_info=True)
        return None

    return output_file

def translate_text(text, target_language, source_language=None, model="nmt"):
    client = create_translate_client()

    project_id = "livevoicetranslation"  # Replace with your actual Google Cloud project ID
    location = "global"  # 'global' can be used for standard models; specify other regions if using a custom model

    parent = f"projects/{project_id}/locations/{location}"

    # You can specify a model if you're using a custom model; otherwise, you can omit this for the default
    if model:
        model_path = f"projects/{project_id}/locations/{location}/models/{model}"
    else:
        model_path = None

    request = {
        "parent": parent,
        "contents": [text],
        "mime_type": "text/plain",  # Mime types: "text/plain" or "text/html"
        "source_language_code": source_language,
        "target_language_code": target_language,
        # "model": model_path # comment out if using base NMT model. Uncomment if using custom model
    }

    response = client.translate_text(request=request)
    if response.translations:
        return response.translations[0].translated_text
    return None


def generate_voice_file(text, voice_id, api_key, model_id="eleven_multilingual_v2", output_file="output_voice.mp3"):
    """Generate a voice file using Eleven Labs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = {
        "model_id": model_id,
        "text": text,
        "voice_settings": {
            "similarity_boost": 0.50,
            "stability": 0.50
        }
    }
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        with open(output_file, 'wb') as file:
            file.write(response.content)
        return output_file
    except Exception as e:
        app.logger.error(f"Error in generating voice file: {e}")
        return None
    
@app.route('/process-audio', methods=['POST'])
def process_audio():
    overall_start_time = time.time()

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file part"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Extract from the request form data
    input_lang = request.form.get('input_lang', 'en-US')  # Default to 'en-US' if not provided
    output_lang = request.form.get('output_lang', 'es')  # Default to 'es' if not provided
    voice_label = request.form.get('voice', 'Juyoung')  # Default to a default voice label if not provided
    voice_id = voices.get(voice_label, 'w0FTld3VgsXqUaNGNRnY')  # Use a default voice ID if the label is not found

    app.logger.debug(f"------------------------------------------------------------")
    app.logger.debug(f"Received Request! Form data: ")
    app.logger.debug(f"Input Lang: {input_lang}")
    app.logger.debug(f"Output Lang: {output_lang}")
    app.logger.debug(f"Voice: {voice_label}")

    try:
        # Save the audio file
        audio_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploaded_audio.wav')
        audio_file.save(audio_file_path)
        save_time = time.time()
        time_to_save_audio = save_time - overall_start_time
        app.logger.debug(f"Time taken for saving audio file: {time_to_save_audio} seconds")

        # Trim the audio file
        audio = AudioSegment.from_file(audio_file_path)
        trimmed_audio = audio[:30000]  # Trim to first 30 seconds
        trimmed_audio_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trimmed_audio.wav')
        trimmed_audio.export(trimmed_audio_path, format="wav")
        trim_time = time.time()
        time_to_trim_audio = trim_time - save_time
        app.logger.debug(f"Time taken for trimming audio file: {time_to_trim_audio} seconds")

        # Transcribe audio
        transcribed_text = transcribe_audio_google(trimmed_audio_path, input_lang) # Using Google Speech-to-Text API
        # transcribed_text = transcribe_audio(trimmed_audio_path) # Using OpenAI API 
        if not transcribed_text:
            return jsonify({"error": "Transcription failed"}), 500
        transcribe_time = time.time()
        time_to_transcribe = transcribe_time - trim_time
        app.logger.debug(f"Time taken for transcription: {time_to_transcribe} seconds")

        # Translate text
        translated_text = translate_text(transcribed_text, output_lang, input_lang)
        if not translated_text:
            return jsonify({"error": "Translation failed"}), 500
        translate_time = time.time()
        time_to_translate = translate_time - transcribe_time
        app.logger.debug(f"Time taken for translation: {time_to_translate} seconds")

        # Generate voice file
        if output_lang == "en":
            model_id = "eleven_turbo_v2"
            voice_file_path = generate_voice_file(translated_text, voice_id, elevenlabs_api_key, model_id)
        else:
            voice_file_path = generate_voice_file(translated_text, voice_id, elevenlabs_api_key)

        if not voice_file_path:
            return jsonify({"error": "Voice generation failed"}), 500
        generate_time = time.time()
        time_to_generate_voice = generate_time - translate_time
        app.logger.debug(f"Time taken for generating voice: {time_to_generate_voice} seconds")

        app.logger.debug(f"Total processing time: {time.time() - overall_start_time} seconds")
        return send_file(voice_file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
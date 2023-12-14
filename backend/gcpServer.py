from flask import Flask, request, jsonify, send_file
import os
import json
import requests
from google.cloud import speech
from google.cloud import translate_v2 as translate

app = Flask(__name__)

# Load configuration from JSON file
with open('config.json') as json_file:
    data = json.load(json_file)
    api_key = data['elevenLabsAPIKey']
    voice_id = data['voiceId']
    translate_from = data['translateFrom']
    translate_to = data['translateTo']

# Set the path to your Google Cloud credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'serviceAccount.json'

def transcribe_audio(speech_file, lang):
    """Transcribe the given audio file using Google Cloud Speech."""
    client = speech.SpeechClient()

    with open(speech_file, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=48000,
        language_code=lang,
    )

    try:
        response = client.recognize(config=config, audio=audio)
    except Exception as e:
        app.logger.error(f"Error in transcribing audio: {e}")
        return None

    for result in response.results:
        return result.alternatives[0].transcript

def translate_text(text, target_language):
    """Translate the given text to the target language using Google Cloud Translation."""
    translate_client = translate.Client()

    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        app.logger.error(f"Error in translating text: {e}")
        return None

def generate_voice_file(text, voice_id, api_key, output_file="output_voice.mp3"):
    """Generate a voice file using Eleven Labs API."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    payload = {
        "model_id": "eleven_monolingual_v1",
        "text": text,
        "voice_settings": {
            "similarity_boost": 0.75,
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
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file part"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        audio_file_path = '/path/to/save/audio_file.wav'  # Update the path
        audio_file.save(audio_file_path)

        transcribed_text = transcribe_audio(audio_file_path, translate_from)
        if transcribed_text is None:
            return jsonify({"error": "Transcription failed"}), 500

        translated_text = translate_text(transcribed_text, translate_to)
        if translated_text is None:
            return jsonify({"error": "Translation failed"}), 500

        voice_file_path = generate_voice_file(translated_text, voice_id, api_key)
        if voice_file_path is None:
            return jsonify({"error": "Voice generation failed"}), 500

        return send_file(voice_file_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Unhandled exception: {e}")
        return jsonify({"error": "An error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

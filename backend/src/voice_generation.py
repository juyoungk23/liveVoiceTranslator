import requests
import logging
import json 
import time
import openai
from .secret_manager import Credentials  # Adjusted import to use the centralized Credentials class

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

credentials = Credentials()  # Create a Credentials instance for centralized management

def get_voice_id(voice, secret_id="ElevenLabsVoiceIDs"):
    voice_ids_json = credentials._fetch_secret(secret_id)  # Use centralized method to get secret
    if not voice_ids_json:
        logger.error("Failed to retrieve voice IDs JSON from Google Secret Manager.")
        return None

    try:
        voice_ids = json.loads(voice_ids_json)
        return voice_ids.get(voice, voice_ids.get("Jarvis"))  # Fallback to "Jarvis" if not found
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode voice IDs JSON: {e}")
        return None

def generate_voice_file_openai(text, voice="onyx", model="tts-1", output_file="output_voice.mp3"):
    api_key = credentials.get_openai_api_key()  # Use centralized method to get API key
    if not api_key:
        logger.error("Failed to retrieve API key for OpenAI voice generation")
        return None

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.audio.speech.create(model=model, voice=voice, input=text)
        response.stream_to_file(output_file)
        return output_file
    except Exception as e:
        logger.error(f"Error in generating voice file with OpenAI: {e}")
        return None
    
def generate_voice_file_eleven_labs(text, voice, model_id="eleven_multilingual_v2", output_file="output_voice.mp3"):
    api_key = credentials.get_elevenlabs_api_key()  # Use centralized method to get API key
    if not api_key:
        logger.error("Failed to retrieve API key for Eleven Labs voice generation")
        return None

    voice_id = get_voice_id(voice)
    if not voice_id:
        logger.error(f"Failed to retrieve voice ID for {voice}")
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "model_id": model_id,
        "text": text,
        "voice_settings": {
            "similarity_boost": 0.8,
            "stability": 0.9,
            "style": 0.10,
            "use_speaker_boost": False
        }
    }
    headers = {"Content-Type": "application/json", "xi-api-key": api_key}

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        with open(output_file, 'wb') as file:
            file.write(response.content)
        return output_file
    except Exception as e:
        logger.error(f"Error in generating voice file with Eleven Labs: {e}")
        return None

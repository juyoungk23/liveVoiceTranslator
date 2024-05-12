import requests
import logging
import json  # Import JSON to handle JSON data
from .secret_manager import get_secret

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the appropriate level if needed
logger.debug("voice_generation.py: Logger level is set to debug")

def get_voice_ids(secret_id="ElevenLabsVoiceIDs"):
    voice_ids_json = get_secret(secret_id)  # This should return a JSON string
    if not voice_ids_json:
        logger.error("Failed to retrieve voice IDs JSON from Google Secret Manager.")
        return None

    try:
        voice_ids = json.loads(voice_ids_json)  # Convert JSON string to a Python dictionary
        return voice_ids
    except json.JSONDecodeError as e:
        logger.error("Failed to decode voice IDs JSON: " + str(e))
        return None

def get_voice_id(voice_name):
    voice_ids = get_voice_ids()
    if voice_ids is None:
        return None

    voice_id = voice_ids.get(voice_name)
    if not voice_id:
        logger.error(f"Voice ID for {voice_name} not found in JSON. Defaulting to Jane.")
        return voice_ids.get("Jane")  # Make sure "Jane" exists or handle the default more robustly

    return voice_id

def generate_voice_file(text, voice_name, api_key_secret_id="ElevenLabsAPIKey", model_id="eleven_multilingual_v2", output_file="output_voice.mp3"):
    api_key = get_secret(api_key_secret_id)
    if not api_key:
        logger.error("Failed to retrieve API key for voice generation")
        return None

    voice_id = get_voice_id(voice_name)
    if not voice_id:
        logger.error(f"Failed to retrieve voice ID for {voice_name}")
        return None

    logger.info(f"Voice ID for {voice_name} found: {voice_id}")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "model_id": model_id,
        "text": text,
        "voice_settings": {
            "similarity_boost": 0.50,
            "stability": 0.50,
            "style": 0.6,
            "use_speaker_boost": True
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
        logger.error(f"Error in generating voice file: {e}")
        return None

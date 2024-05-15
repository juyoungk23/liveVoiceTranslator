import requests
import logging
import json  # Import JSON to handle JSON data
import time
import openai
from .secret_manager import get_secret


# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed
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

def get_voice_id(voice):
    voice_ids = get_voice_ids()
    if voice_ids is None:
        return None

    voice_id = voice_ids.get(voice)
    if not voice_id:
        logger.error(f"Voice ID for {voice} not found in JSON. Defaulting to Jane.")
        return voice_ids.get("Jane")  # Make sure "Jane" exists or handle the default more robustly

    return voice_id

# Define the function to generate voice file using OpenAI's TTS API
def generate_voice_file_openai(text, voice="nova", model="tts-1", output_format="mp3", output_file="output_voice.mp3", api_key_secret_id="OpenAI_API_KEY"):
    api_key = get_secret(api_key_secret_id)
    client = openai.OpenAI(api_key=api_key)  # Pass the API key directly when initializing the client


    if not api_key:
        logger.error("Failed to retrieve API key for OpenAI voice generation")
        return None

    try:

        response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text
        )

        response.stream_to_file(output_file)
        return output_file

    except Exception as e:
        logger.error(f"Error in generating voice file: {e}")
        return None
    
def generate_voice_file_eleven_labs(text, voice, api_key_secret_id="ElevenLabsAPIKey", model_id="eleven_multilingual_v2", output_file="output_voice.mp3"):
    api_key = get_secret(api_key_secret_id)
    if not api_key:
        logger.error("Failed to retrieve API key for voice generation")
        return None

    time_to_retrieve_voice_id = time.time()
    voice_id = get_voice_id(voice)
    if not voice_id:
        logger.error(f"Failed to retrieve voice ID for {voice}")
        return None
    logger.info(f"Voice ID for {voice} found: {voice_id}")
    time_to_retrieve_voice_id = time.time() - time_to_retrieve_voice_id
    logger.info(f"Time to retrieve voice ID: {time_to_retrieve_voice_id:.2f} seconds")

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

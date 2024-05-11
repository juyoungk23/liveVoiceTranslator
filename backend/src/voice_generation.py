import requests
import logging
from .secret_manager import get_secret

def generate_voice_file(text, voice_id, api_key_secret_id="ElevenLabsAPIKey", model_id="eleven_multilingual_v2", output_file="output_voice.mp3"):
    """
    Generate a voice file using Eleven Labs API.
    
    Args:
    text (str): Text to be converted to speech.
    voice_id (str): ID of the voice to use.
    api_key_secret_id (str): Secret ID where the API key is stored.
    model_id (str): ID of the model to use for speech generation, defaults to 'eleven_multilingual_v2'.
    output_file (str): Path where the output file should be saved, defaults to 'output_voice.mp3'.
    
    Returns:
    str or None: Path to the generated voice file or None if failed.
    """
    api_key = get_secret(api_key_secret_id)
    if not api_key:
        logging.error("Failed to retrieve API key for voice generation")
        return None

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
        logging.error(f"Error in generating voice file: {e}")
        return None

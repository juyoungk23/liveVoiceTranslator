import requests
import json
import logging
from pydub import AudioSegment
from pydub.playback import play
import io

# Configure your Eleven Labs API Key and Voice ID here
eleven_labs_api_key = "2c17c500ec63574e4beffcc9fcb3d451"
voice_id = "mQEk9lYcxDbbsCuu6XQJ"

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

def text_to_speech_rest(voice_id, text):
    """
    Sends text to Eleven Labs REST API for TTS and plays back the audio.
    Args:
        voice_id: ID of the voice to use.
        text: Text to be converted to speech.
    """
    logging.info("Sending text to Eleven Labs REST API for TTS.")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {
        "xi-api-key": eleven_labs_api_key,
        "Content-Type": "application/json"
    }

    body = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # or other model as per your requirement
        "voice_settings": {
            "similarity_boost": 0.8,
            "stability": 0.8
            # Add other voice settings if necessary
        }
    }

    response = requests.post(url, headers=headers, json=body, stream=True)

    if response.status_code == 200:
        audio_data = response.content
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
        play(audio_segment)
        logging.info("Audio played successfully.")
    else:
        logging.error(f"Error from Eleven Labs API: {response.status_code} - {response.text}")

# Example usage
def main():
    text_to_speech_rest(voice_id, "Hello, this is a test message.")

if __name__ == "__main__":
    main()

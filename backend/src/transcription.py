# transcription.py
import logging
import os
from google.cloud import speech
from src.audio_processing import convert_audio_to_wav, convert_audio_to_16_bit, get_audio_info
from src.secret_manager import get_credentials
import openai

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed
logger.debug("transcription.py: Logger level is set to debug")


def transcribe_audio_whisper(speech_file, openai_api_key):
    """Transcribe audio using OpenAI's Whisper model."""
    try:
        openai.api_key = openai_api_key
        with open(speech_file, 'rb') as audio_file:
            response = openai.Audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return response.get('text')
    except Exception as e:
        logger.error(f"Error in transcribing audio with Whisper: {e}", exc_info=True)
        return None

def transcribe_audio_google(speech_file, language_code):
    """Transcribe audio using Google Cloud Speech-to-Text API."""
    credentials = get_credentials()
    if not credentials:
        logger.error("Failed to load Google Cloud credentials for Speech-to-Text API")
        return None
    
    client = speech.SpeechClient(credentials=credentials)
    audio_format, sample_rate = get_audio_info(speech_file)
    if not audio_format or not sample_rate:
        logger.error("Failed to retrieve audio format or sample rate")
        return None

    if audio_format not in ['wav', 'mp3']:
        speech_file = convert_audio_to_wav(speech_file)
        if not speech_file:
            return None

    try:
        with open(speech_file, 'rb') as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code
        )
        response = client.recognize(config=config, audio=audio)
        if not response.results:
            logger.error("No transcription results returned from Google Speech-to-Text API")
            return "No text was provided"
        
        transcript = response.results[0].alternatives[0].transcript
        logger.info(f"Transcription successful: {transcript}")
        return transcript
    except Exception as e:
        logger.error(f"Error in Google Cloud transcription: {e}", exc_info=True)
        return None

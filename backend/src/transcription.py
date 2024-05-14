import logging
import os
# from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech
from src.audio_processing import convert_audio_to_wav, get_audio_info
from src.secret_manager import get_gcp_credentials, get_secret
import openai
import time

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def transcribe_audio_whisper(speech_file, openai_api_key="OpenAI_API_KEY"):
    """Transcribe audio using OpenAI's Whisper model."""
    openai_whisper_start_time = time.time()

    try:
        # Load the OpenAI API key from the secret manager
        api_key = get_secret(openai_api_key)
        client = openai.OpenAI(api_key=api_key)  # Pass the API key directly when initializing the client

        time_to_set_api_key = time.time() - openai_whisper_start_time
        logger.info(f"Time to retrieve and set OpenAI API key: {time_to_set_api_key:.2f} seconds")

        with open(speech_file, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

            transcription = response.text
            logger.info(f"Transcription successful: {transcription}")
            return transcription
    except Exception as e:
        logger.error(f"Error in transcribing audio with Whisper: {e}", exc_info=True)
        return None


def transcribe_audio_google(speech_file, language_code, project_id="70513175587", location="global", phrase_set_id="test"):
    """Transcribe audio using Google Cloud Speech-to-Text API with model adaptation."""
    credentials = get_gcp_credentials()
    if not credentials:
        logger.error("Failed to load Google Cloud credentials for Speech-to-Text API")
        return None

    client = speech.SpeechClient(credentials=credentials)

    parent = f"projects/{project_id}/locations/{location}"
    phrase_set_name = f"{parent}/phraseSets/{phrase_set_id}"

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
            language_code=language_code,
            adaptation=speech.SpeechAdaptation(
                phrase_set_references=[phrase_set_name]
            )
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
    
def transcribe_audio_google_backup(speech_file, language_code):
    """Transcribe audio using Google Cloud Speech-to-Text API."""
    credentials = get_gcp_credentials()
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

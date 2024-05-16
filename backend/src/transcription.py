import logging
import time
from google.cloud import speech_v1p1beta1 as speech
from src.audio_processing import convert_audio_to_wav, get_audio_info
from .secret_manager import Credentials

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

prompt_text = "You are a helpful translator for a dental clinic. Review the transcription and ensure all dental terms are spelled correctly and add necessary punctuation. DO NOT reply with anything other than a revised transcription. If *patient or *doctor is present, do not include it in the transcription."

credentials = Credentials()  # Instantiate once and use throughout

def post_process_using_gpt(transcription_text, previous_texts, mode, gpt_model="gpt-4o"):
    """Refine transcription using GPT-4."""
    client = credentials.get_openai_client()
    if not client:
        logger.error("Failed to load OpenAI client")
        return None

    messages = [{"role": "system", "content": prompt_text}] + [
        {"role": "user", "content": f"*{text['person_type']}: {text['text']}"} for text in previous_texts
    ] + [{"role": "system", "content": f"TRANSCRIBE THE FOLLOWING TEXT => *{mode}: {transcription_text}"}]

    try:
        response = client.chat.completions.create(model=gpt_model, messages=messages)
        refined_transcription = response.choices[0].message.content
        logger.info("Post-processing refinement successful.")
        return refined_transcription
    except Exception as e:
        logger.error(f"Error in post-processing transcription with GPT-4: {e}", exc_info=True)
        return None

def transcribe_audio_google(speech_file, language_code, previous_texts, mode, phrase_set_id="test"):
    """Transcribes audio using Google Cloud Speech-to-Text API."""
    speech_client = credentials.get_speech_client()
    if not speech_client:
        logger.error("Failed to load Google Cloud Speech-to-Text client")
        return None

    try:
        audio_format, sample_rate = get_audio_info(speech_file)
        if audio_format not in ['wav', 'mp3']:
            speech_file = convert_audio_to_wav(speech_file)
        if not speech_file:
            return None

        with open(speech_file, 'rb') as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            adaptation=speech.SpeechAdaptation(phrase_set_references=[
                f"projects/{credentials.project_id}/locations/{credentials.location}/phraseSets/{phrase_set_id}"
            ])
        )

        transcription_start_time = time.time()
        response = speech_client.recognize(config=config, audio=audio)
        if not response.results:
            logger.error("No transcription results returned from Google Speech-to-Text API")
            return "No text was provided"

        transcript = response.results[0].alternatives[0].transcript
        logger.info(f"Transcription successful: {transcript}")
        post_processed_text = post_process_using_gpt(transcript, previous_texts, mode)
        logger.info(f"Post-processed transcription: {post_processed_text}")
        return post_processed_text
    except Exception as e:
        logger.error(f"Error in Google Cloud transcription: {e}", exc_info=True)
        return None

def transcribe_audio_whisper(speech_file, previous_texts, mode):
    """Transcribe audio using OpenAI's Whisper model."""
    openai_client = credentials.get_openai_client()
    if not openai_client:
        logger.error("Failed to load OpenAI client")
        return None

    try:
        with open(speech_file, 'rb') as audio_file:
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        transcription = response.text
        logger.info(f"Base transcription using Whisper: {transcription}")
        post_processed_text = post_process_using_gpt(transcription, previous_texts, mode)
        logger.info(f"Post-processed transcription using Whisper: {post_processed_text}")
        return post_processed_text
    except Exception as e:
        logger.error(f"Error in transcribing audio with Whisper: {e}", exc_info=True)
        return None

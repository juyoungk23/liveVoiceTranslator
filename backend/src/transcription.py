import logging
import os
from google.cloud import speech_v1p1beta1 as speech
from src.audio_processing import convert_audio_to_wav, get_audio_info
from src.secret_manager import get_gcp_credentials, get_secret
import openai
import time

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

prompt_text = "You are a helpful translator for a dental clinic. Review the transcription and ensure all dental terms are spelled correctly and add necessary punctuation. DO NOT reply with anything other than a revised transcription. If *patient or *doctor is present, do not include it in the transcription. I need to make it absolutely clear that you should NOT generate any thoughts of your own other than the transcription. You should NOT act that you are either the patient or the doctor. Your ONLY job is to transcribe."

def post_process_using_gpt(transcription_text, system_prompt, client, previousTexts, mode, gpt_model="gpt-4o"):
    """Refine transcription using GPT-4."""

    try:
        logger.info("Starting post-processing with GPT-4...")

        messages = [
            {"role": "system", "content": system_prompt},
            # for each previous text, add it to the messages list.  the content the person_type concantenated with the text
            *[
                {"role": "user", "content": f"*{text['person_type']}: {text['text']}"}
                for text in previousTexts
            ],
            {"role": "user", "content": f"*{mode}: {transcription_text}"}
        ]
        logger.info("Messages: " + str(messages))
        response = client.chat.completions.create(
            model=gpt_model,
            messages=messages
        )
        refined_transcription = response.choices[0].message.content
        logger.info("Refinement successful.")
        return refined_transcription
    except Exception as e:
        logger.error(f"Error in post-processing transcription: {e}", exc_info=True)
        return None
    
def transcribe_audio_google(speech_file, language_code, previousTexts, mode, project_id="70513175587", location="global", phrase_set_id="test"):
    """Transcribe audio using Google Cloud Speech-to-Text API with model adaptation."""
    transcribe_start_time = time.time()  # Start timing the transcription

    credentials = get_gcp_credentials()
    if not credentials:
        logger.error("Failed to load Google Cloud credentials for Speech-to-Text API")
        return None

    client = speech.SpeechClient(credentials=credentials)
    time_to_get_client = time.time() - transcribe_start_time
    logger.info(f"Time to get Google Cloud credentials and client ONLY: {time_to_get_client:.2f} seconds")

    parent = f"projects/{project_id}/locations/{location}"
    phrase_set_name = f"{parent}/phraseSets/{phrase_set_id}"
    phrase_set_name = "projects/70513175587/locations/global/phraseSets/test"

    try:
        transcription_api_start_time = time.time()
        with open(speech_file, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language_code,
            # model="medical_dictation", # does not work with non english languages
            adaptation=speech.SpeechAdaptation(
                phrase_set_references=[phrase_set_name]
            )
        )

        response = client.recognize(config=config, audio=audio)
        if not response.results:
            logger.error("No transcription results returned from Google Speech-to-Text API")
            return "No text was provided"
        
        transcript = response.results[0].alternatives[0].transcript
        transcription_api_end_time = time.time() - transcription_api_start_time
        logger.info(f"Base transcription: {transcript}")
        logger.info(f"Time taken for base transcription ONLY: {time.time() - transcription_api_end_time:.2f} seconds")

        time_to_get_openai_client_start_time = time.time()
        api_key = get_secret("OpenAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        time_to_get_openai_client = time.time() - time_to_get_openai_client_start_time
        logger.info(f"Time to get OpenAI client ONLY: {time_to_get_openai_client:.2f} seconds")

        time_to_post_process_start_time = time.time()
        post_processed_text = post_process_using_gpt(transcript, prompt_text, client, previousTexts, mode)
        time_to_post_process = time.time() - time_to_post_process_start_time
        logger.info(f"Post process text successful: {post_processed_text}")
        logger.info(f"Time to post-process transcription ONLY: {time_to_post_process:.2f} seconds")
        
        total_time_to_transcribe = time.time() - transcribe_start_time
        logger.info(f"Total time to transcribe: {total_time_to_transcribe:.2f} seconds")
        return post_processed_text
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

def transcribe_audio_whisper(speech_file, previousTexts, mode, openai_api_key="OpenAI_API_KEY"):
    """Transcribe audio using OpenAI's Whisper model."""
    transcription_start_time = time.time()  # Start timing the transcription

    try:
        api_key = get_secret(openai_api_key)
        client = openai.OpenAI(api_key=api_key)

        with open(speech_file, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        transcription = response.text
        logger.info(f"Base transcription: {transcription}")
        logger.info(f"Time taken for base transcription: {time.time() - transcription_start_time:.2f} seconds")  # Log time taken

        post_processed_text = post_process_using_gpt(transcription, prompt_text, client, previousTexts)
        logger.info(f"Post-processed transcription: {post_processed_text}")
        return post_processed_text
        
    except Exception as e:
        logger.error(f"Error in transcribing audio with Whisper: {e}", exc_info=True)
        return None

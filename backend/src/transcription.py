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

prompt_text = "You are a helpful translator for a dental clinic. Review the transcription and ensure all dental terms are spelled correctly and add necessary punctuation. Do not reply with anything other than a revised transcription. If *patient or *doctor is present, do not include it in the transcription."

def post_process_using_gpt(transcription_text, system_prompt, client, previousTexts, gpt_model="gpt-4o"):
    """Refine transcription using GPT-4."""
    post_process_start_time = time.time()  # Start timing the post-processing

# Previous texts: [{'text': 'That sounds quite intensive. What exactly does the treatment involve?', 'person_type': 'patient', 'timestamp': DatetimeWithNanoseconds(2024, 5, 15, 8, 22, 45, 92754, tzinfo=datetime.timezone.utc), 'id': 'aGds7GndWGt0yqyE4QUD'}, {'text': 'Your digital radiographs exhibit multifocal periapical lesions and significant alveolar bone loss, particularly around the bicuspid teeth and molars.', 'person_type': 'patient', 'timestamp': DatetimeWithNanoseconds(2024, 5, 15, 8, 21, 43, 507478, tzinfo=datetime.timezone.utc), 'id': 'WUqcvxH9fzz0ry5kzFKG'}]
    try:
        logger.info("Starting post-processing with GPT-4...")

        response = client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                # for each previous text, add it to the messages list.  the content the person_type concantenated with the text
                *[
                    {"role": "user", "content": f"*{text['person_type']}: {text['text']}"}
                    for text in previousTexts
                ],
                {"role": "user", "content": transcription_text}
            ]
        )
        refined_transcription = response.choices[0].message.content
        logger.info("Refinement successful.")
        logger.info(f"Time taken for post-processing: {time.time() - post_process_start_time:.2f} seconds")  # Log time taken
        return refined_transcription
    except Exception as e:
        logger.error(f"Error in post-processing transcription: {e}", exc_info=True)
        return None
    
def transcribe_audio_whisper(speech_file, openai_api_key="OpenAI_API_KEY"):
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

        post_processed_text = post_process_using_gpt(transcription, prompt_text, client)
        logger.info(f"Post-processed transcription: {post_processed_text}")
        return post_processed_text
        
    except Exception as e:
        logger.error(f"Error in transcribing audio with Whisper: {e}", exc_info=True)
        return None

def transcribe_audio_google(speech_file, language_code, previousTexts, project_id="70513175587", location="global", phrase_set_id="test"):
    """Transcribe audio using Google Cloud Speech-to-Text API with model adaptation."""
    
    credentials = get_gcp_credentials()
    if not credentials:
        logger.error("Failed to load Google Cloud credentials for Speech-to-Text API")
        return None

    client = speech.SpeechClient(credentials=credentials)
    logger.info("Google Cloud Speech-to-Text client created successfully")

    parent = f"projects/{project_id}/locations/{location}"
    phrase_set_name = f"{parent}/phraseSets/{phrase_set_id}"
    phrase_set_name = "projects/70513175587/locations/global/phraseSets/test"

    audio_format, sample_rate = get_audio_info(speech_file)
    if not audio_format or not sample_rate:
        logger.error("Failed to retrieve audio format or sample rate")
        return None

    if audio_format not in ['wav', 'mp3']:
        speech_file = convert_audio_to_wav(speech_file)
        if not speech_file:
            return None
        
    logger.info("Audio file preprocessing complete")

    try:
        with open(speech_file, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        logger.info("Audio content loaded successfully")

        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=sample_rate,
            language_code=language_code,
            # model="medical_dictation",
            adaptation=speech.SpeechAdaptation(
                phrase_set_references=[phrase_set_name]
            )
        )
        logger.info("Speech recognition configuration set successfully")

        response = client.recognize(config=config, audio=audio)
        if not response.results:
            logger.error("No transcription results returned from Google Speech-to-Text API")
            return "No text was provided"
        logger.info("Transcription results retrieved successfully")

        transcript = response.results[0].alternatives[0].transcript
        logger.info(f"Transcription successful: {transcript}")
        api_key = get_secret("OpenAI_API_KEY")
        client = openai.OpenAI(api_key=api_key)
        post_processed_text = post_process_using_gpt(transcript, prompt_text, client, previousTexts)
        logger.info(f"Post process successful: {post_processed_text}")
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

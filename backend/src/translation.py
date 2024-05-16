import logging
import time
from .secret_manager import Credentials  # Adjusted import for the centralized Credentials class

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

credentials = Credentials()  # Instantiate credentials for centralized management

def translate_text(text, source_language='en-US', target_language='es', model_id=None):
    """Translates text from one language to another using Google Cloud Translate."""
    translate_start_time = time.time()

    # if source and target languages are the same, then simply return the original text
    if source_language[:2] == target_language[:2]:
        logger.info("Source and target languages are the same. No translation needed.")
        return text

    logger.info(f"Translating text from {source_language} to {target_language}")

    client = credentials.get_translation_client()  # Use centralized method to get Translation client
    if not client:
        logger.error("Failed to load Google Cloud credentials for Translate API")
        return None

    project_id = credentials.project_id  # Use the centralized project_id
    location = credentials.location  # Use the centralized location
    parent = f"projects/{project_id}/locations/{location}"

    # Building the request
    request = {
        "parent": parent,
        "contents": [text],
        "mime_type": "text/plain",  # MIME types: "text/plain" or "text/html"
        "source_language_code": source_language,
        "target_language_code": target_language
    }

    # Adding the model to the request if a custom model ID is provided
    if model_id:
        request["model"] = f"{parent}/models/{model_id}"

    try:
        response = client.translate_text(request)
        if response.translations:
            translation = response.translations[0].translated_text
            logger.info(f"Translated text: {translation}")
            return translation
    except Exception as e:
        logger.error(f"Failed to translate text: {e}", exc_info=True)
        return None

    finally:
        time_to_translate = time.time() - translate_start_time
        logger.info(f"Time to translate: {time_to_translate:.2f} seconds")


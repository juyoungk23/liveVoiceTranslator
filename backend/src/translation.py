# translation.py
import logging
from google.cloud import translate_v3 as translate
from src.secret_manager import get_gcp_credentials

# Ensure the logger uses the same configuration

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed
logger.debug("translation.py: Logger level is set to debug")



def translate_text(text, source_language='en-US', target_language='es', model_id=None):
    """Translates text from one language to another using Google Cloud Translate."""

    translate_start_time = time.time()

    logger.info(f"Translating text from {source_language} to {target_language}")
  
    credentials = get_gcp_credentials()
    if not credentials:
        logger.error("Failed to load Google Cloud credentials for Translate API")
        return None

    time_to_retrieve_credentials = time.time() - translate_start_time
    logger.info(f"Time to retrieve credentials: {time_to_retrieve_credentials:.2f} seconds")
    
    client = translate.TranslationServiceClient(credentials=credentials)
    project_id = "70513175587"  # Replace with your actual project ID
    location = 'global'  # 'global' is the default location; specify other regions if necessary
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
        request["model"] = f"projects/{project_id}/locations/{location}/models/{model_id}"

    try:
        response = client.translate_text(request)
        if response.translations:

            translation = response.translations[0].translated_text
            logger.info(f"Translated text: {translation}")
            return translation
    except Exception as e:
        logger.error(f"Failed to translate text: {e}", exc_info=True)
        return None

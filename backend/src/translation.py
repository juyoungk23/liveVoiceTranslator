# translation.py
import logging
from google.cloud import translate_v3 as translate
from src.secret_manager import get_credentials

def translate_text(text, target_language, source_language='en', model_id=None):
    """Translates text from one language to another using Google Cloud Translate."""
    credentials = get_credentials()
    if not credentials:
        logging.error("Failed to load Google Cloud credentials for Translate API")
        return None

    client = translate.TranslationServiceClient(credentials=credentials)
    project_id = "70513175587"  # Replace with your actual project ID
    location = 'global'  # 'global' is the default location; specify other regions if necessary

    # parent = client.location_path(project_id, location)
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
            return response.translations[0].translated_text
    except Exception as e:
        logging.error(f"Failed to translate text: {e}", exc_info=True)
        return None

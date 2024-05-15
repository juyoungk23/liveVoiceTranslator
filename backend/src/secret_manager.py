import logging
import json
from google.cloud import secretmanager, speech_v1p1beta1 as speech, translate_v3 as translate
from google.oauth2 import service_account
import openai

# Configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Credentials:
    def __init__(self, project_id="70513175587", location='global'):
        self.project_id = project_id
        self.location = location
        self.google_secret_id = "cloud-translation-service-account"
        self.openai_api_key_secret_id = "OpenAI_API_KEY"
        self.client = secretmanager.SecretManagerServiceClient()
        
        # Cached properties
        self._gcp_credentials = None
        self._openai_api_key = None
        self._speech_client = None
        self._translation_client = None
        self._openai_client = None

    def _fetch_secret(self, secret_id):
        """Internal method to retrieve secrets to avoid duplicate calls."""
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            secret_data = response.payload.data.decode('UTF-8')
            return secret_data
        except Exception as e:
            logger.error(f"Failed to access secret {secret_id}: {e}", exc_info=True)
            return None

    def get_gcp_credentials(self):
        """Returns cached GCP credentials or fetches them if not already done."""
        if not self._gcp_credentials:
            secret_data = self._fetch_secret(self.google_secret_id)
            if secret_data:
                try:
                    credentials_info = json.loads(secret_data)
                    self._gcp_credentials = service_account.Credentials.from_service_account_info(credentials_info)
                except Exception as e:
                    logger.error(f"Failed to construct credentials from secret {self.google_secret_id}: {e}", exc_info=True)
        return self._gcp_credentials

    def get_openai_api_key(self):
        """Returns cached OpenAI API key or fetches it if not already done."""
        if not self._openai_api_key:
            self._openai_api_key = self._fetch_secret(self.openai_api_key_secret_id)
        return self._openai_api_key

    def get_speech_client(self):
        """Returns a cached Speech-to-Text client or creates it if not already done."""
        if not self._speech_client:
            credentials = self.get_gcp_credentials()
            if credentials:
                self._speech_client = speech.SpeechClient(credentials=credentials)
        return self._speech_client

    def get_translation_client(self):
        """Returns a cached Translation client or creates it if not already done."""
        if not self._translation_client:
            credentials = self.get_gcp_credentials()
            if credentials:
                self._translation_client = translate.TranslationServiceClient(credentials=credentials)
        return self._translation_client

    def get_openai_client(self):
        """Returns a cached OpenAI client or creates it if not already done."""
        if not self._openai_client:
            api_key = self.get_openai_api_key()
            if api_key:
                self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client

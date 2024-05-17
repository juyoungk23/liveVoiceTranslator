import logging
import json
from google.cloud import secretmanager, speech_v1p1beta1 as speech, translate_v3 as translate, firestore
from google.oauth2 import service_account
import openai
from deepgram import DeepgramClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Credentials:
    def __init__(self, project_id="70513175587", location='global'):
        self.project_id = project_id
        self.location = location
        self.google_secret_id = "cloud-translation-service-account"
        self.openai_api_key_secret_id = "OpenAI_API_KEY"
        self.elevenlabs_key_secret_id = "ElevenLabsAPIKey"
        self.deepgram_key_secret_id = "DeepgramTestAPIKey"
        self.client = secretmanager.SecretManagerServiceClient()
        
        self._gcp_credentials = None
        self._openai_api_key = None
        self._elevenlabs_api_key = None
        self._speech_client = None
        self._translation_client = None
        self._openai_client = None
        self._deepgram_client = None
        self._firestore_client = None

    def _fetch_secret(self, secret_id):
        secret_name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
        try:
            response = self.client.access_secret_version(request={"name": secret_name})
            secret_data = response.payload.data.decode('UTF-8')
            return secret_data
        except Exception as e:
            logger.error(f"Failed to access secret {secret_id}: {e}")
            return None

    def get_gcp_credentials(self):
        if not self._gcp_credentials:
            secret_data = self._fetch_secret(self.google_secret_id)
            if secret_data:
                try:
                    credentials_info = json.loads(secret_data)
                    self._gcp_credentials = service_account.Credentials.from_service_account_info(credentials_info)
                except Exception as e:
                    logger.error(f"Failed to construct credentials from secret {self.google_secret_id}: {e}")
        return self._gcp_credentials

    def get_openai_api_key(self):
        if not self._openai_api_key:
            self._openai_api_key = self._fetch_secret(self.openai_api_key_secret_id)
        return self._openai_api_key

    def get_elevenlabs_api_key(self):
        if not self._elevenlabs_api_key:
            self._elevenlabs_api_key = self._fetch_secret(self.elevenlabs_key_secret_id)
        return self._elevenlabs_api_key
    
    def get_speech_client(self):
        if not self._speech_client and self.get_gcp_credentials():
            self._speech_client = speech.SpeechClient(credentials=self._gcp_credentials)
        return self._speech_client

    def get_translation_client(self):
        if not self._translation_client and self.get_gcp_credentials():
            self._translation_client = translate.TranslationServiceClient(credentials=self._gcp_credentials)
        return self._translation_client

    def get_openai_client(self):
        if not self._openai_client and self.get_openai_api_key():
            self._openai_client = openai.OpenAI(api_key=self._openai_api_key)
        return self._openai_client

    def get_firestore_client(self):
        if not self._firestore_client:
            if self.get_gcp_credentials():
                self._firestore_client = firestore.Client()
        return self._firestore_client

    def get_deepgram_client(self):
        if not self._deepgram_client:
            deepgram_api_key = self._fetch_secret(self.deepgram_key_secret_id)
            if deepgram_api_key:
                self._deepgram_client = DeepgramClient(deepgram_api_key)
        return self._deepgram_client

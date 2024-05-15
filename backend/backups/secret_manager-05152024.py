# secret_manager.py
from google.cloud import secretmanager
from google.oauth2 import service_account
import json
import logging

# Ensure the logger uses the same configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed
logger.debug("secret_manager.py: Logger level is set to debug")


# Configure your Google Cloud Project ID here
PROJECT_ID = "70513175587"
GOOGLE_SECRET_ID = "cloud-translation-service-account"

def get_secret(secret_id):
    """Retrieves the latest version of a secret from Google Cloud Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": secret_name})
        secret_data = response.payload.data.decode('UTF-8')
        return secret_data
    except Exception as e:
        logger.error(f"Failed to access secret {secret_id}: {e}", exc_info=True)
        return None

def get_gcp_credentials():
    """Fetches and constructs service account credentials from a secret."""
    secret_data = get_secret(GOOGLE_SECRET_ID)
    if not secret_data:
        return None
    try:
        credentials_info = json.loads(secret_data)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return credentials
    except Exception as e:
        logger.error(f"Failed to construct credentials from secret {GOOGLE_SECRET_ID}: {e}", exc_info=True)
        return None

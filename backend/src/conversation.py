import datetime
import logging
import time
import google.cloud.firestore as firestore
from .secret_manager import Credentials  # Adjusted import for the centralized Credentials class

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

credentials = Credentials()  # Instantiate credentials

def delete_all_conversations():
    db = credentials.get_firestore_client()
    conversation_collection = db.collection('conversation')
    docs = conversation_collection.stream()
    for doc in docs:
        logger.info(f"Deleting {doc.id}")
        doc.reference.delete()
    logger.info("All conversations have been deleted.")

def get_last_three_conversations():
    db = credentials.get_firestore_client()
    conversation_collection = db.collection('conversation')
    query = conversation_collection.where('person_type', 'in', ['doctor', 'patient'])
    results = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(3).stream()
    conversations = []
    for doc in results:
        data = doc.to_dict()
        data['id'] = doc.id
        conversations.insert(0, data)
    return conversations

def add_conversation(text, person_type):
    db = credentials.get_firestore_client()
    conversation_collection = db.collection('conversation')
    document_data = {
        'text': text,
        'person_type': person_type,
        'timestamp': datetime.datetime.now()
    }
    doc_ref = conversation_collection.add(document_data)
    logger.info(f"Added new conversation with ID: {doc_ref[1].id}")

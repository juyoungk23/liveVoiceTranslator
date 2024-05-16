import google.cloud.firestore as firestore
import datetime
import logging
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Set the appropriate level if needed

def delete_all_conversations():
    db = firestore.Client()
    conversation_collection = db.collection('conversation')
    # Retrieve all documents in the collection
    docs = conversation_collection.stream()
    # Delete documents in batches
    for doc in docs:
        logger.info(f"Deleting {doc.id}")
        doc.reference.delete()
    logger.info("All conversations have been deleted.")

def get_last_three_conversations():
    """Retrieves the last three conversations from the Firestore collection."""
    time_to_get_conversations = time.time()
    db = firestore.Client()
    conversation_collection = db.collection('conversation')

    # Query the last three entries with person_type 'doctor' or 'patient'
    query = conversation_collection.where('person_type', 'in', ['doctor', 'patient'])
    results = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(3).stream()

    conversations = []
    for doc in results:
        data = doc.to_dict()
        data['id'] = doc.id
        conversations.insert(0, data)
    time_to_get_conversations = time.time() - time_to_get_conversations
    logger.info(f"Time to get conversations: {time_to_get_conversations:.2f} seconds")
    return conversations

def add_conversation(text, person_type):
    """Adds a new conversation to the Firestore collection."""
    time_to_add_conversation = time.time()
    db = firestore.Client()
    conversation_collection = db.collection('conversation')
    time_to_retrieve_collection = time.time() - time_to_add_conversation
    logger.info(f"Time to retrieve collection: {time_to_retrieve_collection:.2f} seconds")

    if person_type not in ['doctor', 'patient']:
        raise ValueError("person_type must be 'doctor' or 'patient'")

    # Create a new document
    document_data = {
        'text': text,
        'person_type': person_type,
        'timestamp': datetime.datetime.now()  # Use current time as the timestamp
    }
    # Add document to Firestore
    doc_ref = conversation_collection.add(document_data)
    logger.info(f"Added new conversation with ID: {doc_ref[1].id}")
    time_to_add_conversation = time.time() - time_to_add_conversation
    logger.info(f"Time to add conversation: {time_to_add_conversation:.2f} seconds")

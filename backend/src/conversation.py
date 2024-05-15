import google.cloud.firestore as firestore
import datetime

def delete_all_conversations():
    db = firestore.Client()
    conversation_collection = db.collection('conversation')
    # Retrieve all documents in the collection
    docs = conversation_collection.stream()
    # Delete documents in batches
    for doc in docs:
        print(f"Deleting {doc.id}")
        doc.reference.delete()
    print("All conversations have been deleted.")

def get_last_three_conversations():
    db = firestore.Client()
    conversation_collection = db.collection('conversation')

    # Query the last three entries with person_type 'doctor' or 'patient'
    query = conversation_collection.where('person_type', 'in', ['doctor', 'patient'])
    results = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(3).stream()
    
    conversations = []
    for doc in results:
        data = doc.to_dict()
        data['id'] = doc.id  # Include document ID in the data
        conversations.append(data)

    stringed_conversations = [f"{c['person_type']}: {c['text']}" for c in conversations]
    return conversations

def add_conversation(text, person_type):
    """Adds a new conversation to the Firestore collection."""
    db = firestore.Client()
    conversation_collection = db.collection('conversation')

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
    print(f"Added new conversation with ID: {doc_ref[1].id}")

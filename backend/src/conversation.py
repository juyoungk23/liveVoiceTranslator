import google.cloud.firestore as firestore
import datetime

class ConversationHandler:
    def __init__(self):
        # Initialize the Firestore client
        self.db = firestore.Client()
        # Reference to the conversation collection
        self.conversation_collection = self.db.collection('conversation')

    def delete_all_conversations(self):
        # Retrieve all documents in the collection
        docs = self.conversation_collection.stream()
        # Delete documents in batches
        for doc in docs:
            print(f"Deleting {doc.id}")
            doc.reference.delete()
        print("All conversations have been deleted.")

    def get_last_three_conversations(self):
        # Query the last three entries with person_type 'doctor' or 'patient'
        query = self.conversation_collection.where('person_type', 'in', ['doctor', 'patient'])
        results = query.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(3).stream()
        
        conversations = []
        for doc in results:
            data = doc.to_dict()
            data['id'] = doc.id  # Include document ID in the data
            conversations.append(data)

        stringed_conversations = [f"{c['person_type']}: {c['text']}" for c in conversations]
        return stringed_conversations

    def add_conversation(self, text, person_type):
        """Adds a new conversation to the Firestore collection."""
        if person_type not in ['doctor', 'patient']:
            raise ValueError("person_type must be 'doctor' or 'patient'")

        # Create a new document
        document_data = {
            'text': text,
            'person_type': person_type,
            'timestamp': datetime.datetime.now()  # Use current time as the timestamp
        }
        # Add document to Firestore
        doc_ref = self.conversation_collection.add(document_data)
        print(f"Added new conversation with ID: {doc_ref[1].id}")

from datetime import datetime
import firebase_admin
from firebase_admin import firestore, credentials


class FirestoreHandler(object):
    COLLECTION = 'state'
    def __init__(self, cred: dict) -> None:
        firebase_admin.initialize_app(
            credential=credentials.Certificate(
                cert=cred,
            )
        )
        self.db = firestore.client()

    def add_record(self, record: dict) -> None:
        record.pop('raw_image', None)
        self.db.collection(self.COLLECTION).document(record['sn_nema']).set(
            record
        )

    def update_record(self, old_record: dict, new_record: dict):
        new_record.pop('raw_image', None)
        self.db.collection(self.COLLECTION).document(
            old_record['sn_nema'],
        ).update(new_record)

    def get_all_records(self):
        return [record._data for record in self.db.collection(self.COLLECTION).get()]

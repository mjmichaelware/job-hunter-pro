_db = None

def get_db():
    global _db
    if _db is None:
        try:
            from google.cloud import firestore
            _db = firestore.Client()
        except ImportError:
            raise RuntimeError("google-cloud-firestore is not installed. Database operations are unavailable.")
    return _db

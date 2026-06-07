from store.repository import BaseRepository

class BatchesRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("batches", db)

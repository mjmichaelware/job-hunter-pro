from store.repository import BaseRepository

class ApplicationsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("applications", db)

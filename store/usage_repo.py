from store.repository import BaseRepository

class UsageRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("usage", db)

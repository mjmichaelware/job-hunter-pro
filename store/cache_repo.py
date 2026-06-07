from store.repository import BaseRepository

class CacheRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("cache", db)

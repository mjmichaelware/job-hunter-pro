from store.repository import BaseRepository

class PlacesRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("places", db)

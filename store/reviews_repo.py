from store.repository import BaseRepository

class ReviewsRepository(BaseRepository):
    def __init__(self, db=None):
        super().__init__("reviews", db)

from flask import jsonify
from api import api_bp
from store.batches_repo import BatchesRepository

@api_bp.route('/history', methods=['GET'])
def history():
    """Returns a list of historical ingestion batches."""
    repo = BatchesRepository()
    batches = repo.get_all()
    return jsonify({"batches": batches})

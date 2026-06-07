from flask import jsonify, request
from api import api_bp
from store.applications_repo import ApplicationsRepository
from models.application import Application
from core.clock import utc_now_iso

# Shared instance for the blueprint
repo = ApplicationsRepository()

@api_bp.route('/applications', methods=['GET'])
def get_applications():
    """Retrieves all application records."""
    apps = repo.get_all()
    return jsonify({"applications": apps})

@api_bp.route('/applications', methods=['POST'])
def create_application():
    """Creates a new application record."""
    data = request.get_json()
    if not data or "job_id" not in data:
        return jsonify({"error": "Missing job_id"}), 400
    
    job_id = data["job_id"]
    now = utc_now_iso()
    
    # Check if already exists
    existing = repo.get_by_id(job_id)
    if existing:
        return jsonify({"error": "Application already exists for this job"}), 409

    # Build model
    app_data = {
        "job_id": job_id,
        "status": data.get("status", "DISCOVERED"),
        "notes": data.get("notes", ""),
        "created_at": now,
        "updated_at": now
    }
    
    try:
        app_obj = Application(**app_data)
        repo.save_application(job_id, app_obj.model_dump())
        return jsonify(app_obj.model_dump()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@api_bp.route('/applications/<job_id>', methods=['GET'])
def get_application(job_id):
    """Retrieves a single application by job_id."""
    app_data = repo.get_by_id(job_id)
    if not app_data:
        return jsonify({"error": "Not found"}), 404
    return jsonify(app_data)

@api_bp.route('/applications/<job_id>', methods=['PATCH'])
def update_application(job_id):
    """Updates an existing application record (status, notes)."""
    existing = repo.get_by_id(job_id)
    if not existing:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Update fields
    if "status" in data:
        existing["status"] = data["status"]
    if "notes" in data:
        existing["notes"] = data["notes"]
    
    existing["updated_at"] = utc_now_iso()
    
    try:
        app_obj = Application(**existing)
        repo.save_application(job_id, app_obj.model_dump())
        return jsonify(app_obj.model_dump()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

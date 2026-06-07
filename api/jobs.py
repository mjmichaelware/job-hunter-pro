from flask import jsonify, request
from api import api_bp
from store.jobs_repo import JobsRepository

@api_bp.route('/jobs', methods=['GET'])
def jobs():
    """
    Returns accepted job listings.
    Supports dry_run parameter to return query plan without discovery.
    """
    dry_run = request.args.get('dry_run') == '1'
    
    if dry_run:
        return jsonify({
            "mode": "dry_run",
            "plan": "Discovery query plan (mocked)",
            "estimated_cost": 0.0,
            "jobs": []
        })

    # For live discovery, this would trigger a run. 
    # For this endpoint, we return stored jobs.
    repo = JobsRepository()
    all_jobs = repo.get_all()
    accepted_jobs = [j for j in all_jobs if j.get('status') == 'accepted']
    
    return jsonify({
        "mode": "live",
        "jobs": accepted_jobs
    })

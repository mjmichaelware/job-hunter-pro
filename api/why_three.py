from flask import jsonify
from api import api_bp
from store.jobs_repo import JobsRepository

@api_bp.route('/why-three', methods=['GET'])
def why_three():
    """Returns the top 3 candidates with resonance match details."""
    repo = JobsRepository()
    all_jobs = repo.get_all()
    # Mocking resonance score for now if not present
    for j in all_jobs:
        if 'resonance_score' not in j:
            j['resonance_score'] = j.get('match_score', 0)
            j['why_included'] = "High match score with local resonance."

    top3 = sorted(all_jobs, key=lambda x: x.get('resonance_score', 0), reverse=True)[:3]
    
    return jsonify({"top3": top3})

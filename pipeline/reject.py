from typing import Dict, Any, Optional

def reject_early(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Checks if a job should be rejected before expensive enrichment.
    Returns rejection info if rejected, else None.
    """
    title = job.get("title", "").strip()
    if not title:
        return {"reason": "empty_title", "details": "Job title is empty or whitespace."}
    
    # Example: reject generic recruiter titles if needed
    if "recruiter" in title.lower() and "hiring" not in title.lower():
        # But wait, we want to be multi-industry. 
        # Maybe just keep it simple for now.
        pass

    return None

def reject_late(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Checks if a job should be rejected after enrichment and scoring.
    Returns rejection info if rejected, else None.
    """
    # Industry mismatch
    if job.get("industry") == "unknown":
        return {"reason": "not_mapped_to_industry", "details": "Job text did not match any registered industry taxonomy."}

    # Match score too low
    match_score = job.get("match_score", 0)
    if match_score < 40: # Lowered threshold for multi-industry broadness
        return {
            "reason": "low_match_score", 
            "details": f"Match score {match_score} is below the acceptance threshold of 40."
        }

    return None

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
    Unknown industry and low match scores are kept — they surface to the user
    who can filter in the UI. Only true hard failures are rejected here.
    """
    return None

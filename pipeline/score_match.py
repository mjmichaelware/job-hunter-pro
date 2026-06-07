from typing import Dict, Any

def score_match(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates a heuristic match score based on title and description.
    Provides industry-specific bonuses.
    """
    score = 50 # Baseline
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    industry = job.get("industry", "unknown")
    
    # Industry-specific relevance
    if industry == "food_service":
        if any(term in text for term in ["cook", "chef", "server", "barista"]):
            score += 20
    elif industry == "hospitality":
        if any(term in text for term in ["hotel", "front desk", "concierge"]):
            score += 20
    elif industry == "care_social":
        if any(term in text for term in ["peer support", "behavioral", "social"]):
            score += 20
    elif industry == "customer_service":
        if any(term in text for term in ["call center", "support", "client"]):
            score += 20
    elif industry == "sales":
        if any(term in text for term in ["sales", "account executive", "bdr"]):
            score += 20
    elif industry == "retail_ops":
        if any(term in text for term in ["cashier", "stocking", "retail"]):
            score += 20

    # General quality signals
    if job.get("url"):
        score += 5
    if len(job.get("description", "")) > 100:
        score += 5
        
    job["match_score"] = min(100, score)
    return job

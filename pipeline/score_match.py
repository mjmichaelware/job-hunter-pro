def score_match(job: dict) -> dict:
    score = 50
    title = job.get("title", "").lower()
    desc = job.get("description", "").lower()
    
    if "engineer" in title or "developer" in title:
        score += 20
    if "python" in desc or "react" in desc:
        score += 20
        
    job["match_score"] = min(100, score)
    return job

def classify(job: dict) -> dict:
    # Use full candidate meaning (title + description), not only title keywords.
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    industry = "unknown"
    
    if "software" in text or "code" in text or "developer" in text:
        industry = "software"
    elif "sale" in text or "account executive" in text:
        industry = "sales"
    elif "care" in text or "nurse" in text:
        industry = "healthcare"
        
    job["industry"] = industry
    return job

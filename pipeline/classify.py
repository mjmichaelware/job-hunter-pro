from typing import Dict, Any, Optional
from industries import classify_text

def classify(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classifies a job into one of the registered industries.
    Uses deterministic text matching from the industries package.
    """
    # Combine title and description for classification
    text = f"{job.get('title', '')} {job.get('description', '')}"
    
    industry_key = classify_text(text)
    
    # Store result in job dict
    job["industry"] = industry_key or "unknown"
    
    return job

import hashlib
from typing import List, Dict, Any

def generate_canonical_key(job: Dict[str, Any]) -> str:
    """
    Generates a deterministic SHA-256 key based on title, company, and URL.
    This identifies the same job across different providers.
    """
    # Clean and normalize strings for hashing
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()
    url = job.get("url", "").strip().lower()
    
    key_str = f"{title}|{company}|{url}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

def dedupe(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Removes duplicate jobs from a list based on their canonical key.
    Preserves the first occurrence found.
    """
    seen = set()
    unique_jobs = []
    
    for job in jobs:
        key = generate_canonical_key(job)
        if key not in seen:
            seen.add(key)
            job["canonical_key"] = key
            unique_jobs.append(job)
            
    return unique_jobs

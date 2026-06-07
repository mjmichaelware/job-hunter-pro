import hashlib

def generate_canonical_key(job: dict) -> str:
    key_str = f"{job.get('title', '')}|{job.get('company', '')}|{job.get('resolved_place', '')}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()

def dedupe(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = generate_canonical_key(job)
        if key not in seen:
            seen.add(key)
            job["canonical_key"] = key
            unique_jobs.append(job)
    return unique_jobs

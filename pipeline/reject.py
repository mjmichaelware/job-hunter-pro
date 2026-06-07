def reject_early(job: dict) -> bool:
    title = job.get("title", "").strip()
    if not title:
        job["reject_reason"] = "empty title"
        return True
    if "spam" in title.lower():
        job["reject_reason"] = "spam keyword in title"
        return True
    return False

def reject_late(job: dict) -> bool:
    if job.get("match_score", 0) < 60:
        job["reject_reason"] = "match score too low"
        return True
    return False

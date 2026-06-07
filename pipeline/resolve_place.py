def resolve_place(job: dict) -> dict:
    # Deterministic dummy resolution without live calls
    loc = job.get("location", "").strip().lower()
    if not loc:
        job["resolved_place"] = None
    else:
        job["resolved_place"] = f"resolved_{loc}"
    return job

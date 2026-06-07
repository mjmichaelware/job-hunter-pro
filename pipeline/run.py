import logging
from typing import List, Dict, Any, Union
from models import SearchResult
from pipeline.normalize import normalize_job
from pipeline.reject import reject_early, reject_late
from pipeline.resolve_place import resolve_place
from pipeline.classify import classify
from pipeline.score_match import score_match
from pipeline.score_review import score_review
from pipeline.dedupe import dedupe

logger = logging.getLogger(__name__)

def run_pipeline(raw_results: List[Union[dict, SearchResult]]) -> Dict[str, Any]:
    """
    Orchestrates the multi-industry job pipeline.
    Accepts raw dicts or SearchResult objects.
    Returns structured results with counts and rejection evidence.
    """
    accepted = []
    rejected = []
    
    counts = {
        "raw": len(raw_results),
        "accepted": 0,
        "rejected": 0,
        "rejection_reasons": {}
    }

    # 1. Normalize
    normalized_jobs = []
    for raw in raw_results:
        job = normalize_job(raw)
        
        # 2. Early Reject
        rejection = reject_early(job)
        if rejection:
            job["status"] = "rejected"
            job["rejection"] = rejection
            rejected.append(job)
            reason = rejection["reason"]
            counts["rejection_reasons"][reason] = counts["rejection_reasons"].get(reason, 0) + 1
            continue
            
        normalized_jobs.append(job)

    # 3. Dedupe normalized set
    # (Optional: dedupe early to save enrichment costs)
    normalized_jobs = dedupe(normalized_jobs)

    # 4. Enrich & Classify
    for job in normalized_jobs:
        # Resolve Place (Dummy for now)
        job = resolve_place(job)
        
        # Multi-Industry Classification (R1 Registry)
        job = classify(job)
        
        # Scoring
        job = score_match(job)
        job = score_review(job)
        
        # 5. Late Reject
        rejection = reject_late(job)
        if rejection:
            job["status"] = "rejected"
            job["rejection"] = rejection
            rejected.append(job)
            reason = rejection["reason"]
            counts["rejection_reasons"][reason] = counts["rejection_reasons"].get(reason, 0) + 1
            continue
            
        job["status"] = "accepted"
        accepted.append(job)

    # Final counts
    counts["accepted"] = len(accepted)
    counts["rejected"] = len(rejected)
    
    return {
        "accepted": accepted,
        "rejected": rejected,
        "counts": counts
    }

from pipeline.normalize import normalize_job
from pipeline.reject import reject_early, reject_late
from pipeline.resolve_place import resolve_place
from pipeline.classify import classify
from pipeline.score_match import score_match
from pipeline.score_review import score_review
from pipeline.dedupe import dedupe

def run_pipeline(raw_jobs: list[dict], provider: str = "test") -> list[dict]:
    results = []
    
    # Early phase
    for raw in raw_jobs:
        job = normalize_job(raw, provider)
        if reject_early(job):
            continue
            
        # Enrichment & late phase
        job = resolve_place(job)
        job = classify(job)
        job = score_match(job)
        job = score_review(job)
        
        if reject_late(job):
            continue
            
        results.append(job)
        
    # Dedupe final results
    return dedupe(results)

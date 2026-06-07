from typing import Dict, Any

def score_review(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements the authoritative review scoring formula:
    60% rating, 15% count, 15% sentiment, 10% consistency.
    Caps low star ratings so they cannot achieve high scores.
    """
    # If no place/review data, return baseline
    place = job.get("place_data")
    if not place:
        job["review_score"] = 0
        return job

    rating = place.get("rating", 0.0)
    count = place.get("review_count", 0)
    
    # 1. Rating Component (60%)
    # Scale 1.0-5.0 to 0-100
    rating_score = (max(0, rating - 1.0) / 4.0) * 100
    
    # 2. Count Component (15%)
    # Logarithmic scaling, 100+ reviews is full marks
    import math
    count_score = min(100, (math.log10(count + 1) / math.log10(101)) * 100) if count > 0 else 0
    
    # 3. Sentiment & 4. Consistency (Placeholders for now)
    sentiment_score = 70 
    consistency_score = 80
    
    final_score = (
        (rating_score * 0.60) +
        (count_score * 0.15) +
        (sentiment_score * 0.15) +
        (consistency_score * 0.10)
    )
    
    # Low rating caps
    if rating < 3.5:
        final_score = min(final_score, 40)
    elif rating < 3.8:
        final_score = min(final_score, 60)
    elif rating < 4.2:
        final_score = min(final_score, 80)
        
    job["review_score"] = round(final_score, 1)
    return job

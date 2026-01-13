
"""
Step 4 - Logic Engine:
Filters and ranks studies based on relevance to the user
"""
def score_studies(studies, user_age):
    scored_studies = []
    
    print(f"DEBUG: Scoring {len(studies)} studies for Age {user_age}...")

    for study in studies:
        score = 0
        reasons = []

        # CRITERIA 1: STUDY DESIGN
        sType = study.get('study_type', '').lower()
        if "meta-analysis" in sType or "systematic review" in sType:
            score += 15
            reasons.append("High Quality (Meta/Review)")
        elif "rct" in sType or "randomized" in sType:
            score += 10
            reasons.append("High Quality (RCT)")
        else:
            score += 2 # Basic baseline for existing
        
        # CRITERIA 2: AGE RELEVANCE
        min_a = study.get('min_age')
        max_a = study.get('max_age')
        mean_a = study.get('mean_age')
        
        age_hit = False
        
        # Check Range Match (e.g. User 25 falls inside 18-35)
        if min_a is not None and max_a is not None:
            if min_a <= user_age <= max_a:
                score += 10
                reasons.append("Direct Age Range Match")
                age_hit = True
        
        # Check Mean Match (e.g. User 25 is close to Mean 24)
        # Only if haven't hit range bonus
        if not age_hit and mean_a is not None:
            if abs(mean_a - user_age) <= 5: # Within 5 years
                score += 10
                reasons.append("Close to Mean Age")
            elif abs(mean_a - user_age) <= 10: # Within 10 years
                score += 5
                reasons.append("Loose Age Match")

        # CRITERIA 3: SAMPLE SIZE (tie-breaker)
        n = study.get('n')
        if n and n > 100:
            score += 5
            reasons.append("Large Sample Size")
        elif n and n > 30:
            score += 2

        # Final Bundle
        # Keep original data but add the score
        study['relevance_score'] = score
        study['scoring_reasons'] = ", ".join(reasons)
        scored_studies.append(study)

    # Sort by Score (highest first)
    scored_studies.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Return Top 5
    return scored_studies[:5]

# Test Block
if __name__ == "__main__":
    # Mock data output from Step 3
    mock_extracted = [
        {
            "id": "111", 
            "study_type": "RCT", 
            "mean_age": 22, 
            "n": 30, 
            "outcome_summary": "Good for young athletes"
        },
        {
            "id": "222", 
            "study_type": "RCT", 
            "min_age": 60, 
            "max_age": 80, 
            "n": 500, 
            "outcome_summary": "Good for elderly"
        },
        {
            "id": "333", 
            "study_type": "Meta-Analysis", 
            "mean_age": 25, 
            "n": 2000, 
            "outcome_summary": "General population data"
        }
    ]
    
    user_age = 24
    print(f"Testing Scorer for User Age: {user_age}\n")
    
    ranked = score_studies(mock_extracted, user_age)
    
    for i, s in enumerate(ranked):
        print(f"#{i+1} [Score: {s['relevance_score']}] ID: {s['id']} ({s['study_type']})")
        print(f"   Reasons: {s['scoring_reasons']}")
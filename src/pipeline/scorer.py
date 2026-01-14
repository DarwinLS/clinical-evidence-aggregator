"""
Step 4: The Logic Engine.
Filters and ranks studies based on Relevance (Goal Match) + Quality + Age + Size.
"""
def score_studies(studies, user_age, goal="general"):

    scored_studies = []
    
    # Define keywords for boosting based on user goal
    keywords = {
        "strength": ["muscle", "hypertrophy", "strength", "power", "sprint", "athletic", "exercise", "resistance", "anaerobic"],
        "cognition": ["memory", "brain", "cognitive", "depression", "anxiety", "mood", "mental", "neuro", "focus", "attention"],
        "general": [] # relies purely on study quality/age
    }
    
    target_keywords = keywords.get(goal, [])
    
    print(f"DEBUG: Scoring {len(studies)} studies for Age {user_age}, Goal: '{goal}'...")

    for study in studies:
        score = 0
        reasons = []

        # CRITERIA 1: GOAL MATCH
        # If the user has a specific goal, heavily boost matching studies.
        # Check both the title and the outcome summary.
        text_blob = (study.get('title', '') + " " + study.get('outcome_summary', '')).lower()
        
        if target_keywords:
            if any(word in text_blob for word in target_keywords):
                score += 20  # Huge bonus to ensure relevant topics bubble up
                reasons.append(f"Matches Goal: {goal}")

        # CRITERIA 2: STUDY DESIGN (Quality)
        sType = study.get('study_type', '').lower()
        if "meta-analysis" in sType or "systematic review" in sType:
            score += 15
            reasons.append("High Quality (Meta/Review)")
        elif "rct" in sType or "randomized" in sType:
            score += 10
            reasons.append("High Quality (RCT)")
        else:
            score += 2 # Basic baseline so no 0-score studies
        
        # CRITERIA 3: AGE RELEVANCE
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
        if not age_hit and mean_a is not None:
            if abs(mean_a - user_age) <= 5: # Within 5 years
                score += 10
                reasons.append("Close to Mean Age")
            elif abs(mean_a - user_age) <= 10: # Within 10 years
                score += 5
                reasons.append("Loose Age Match")

        # CRITERIA 4: SAMPLE SIZE (Tie-Breaker)
        n = study.get('n')
        # Ensure n is treated as an integer
        try:
            if n:
                n_val = int(n)
                if n_val > 100:
                    score += 5
                    reasons.append("Large Sample Size")
                elif n_val > 30:
                    score += 2
        except:
            pass # If n is 'N/A' or weird format, ignore it

        # Final Bundle
        study['relevance_score'] = score
        study['scoring_reasons'] = ", ".join(reasons)
        scored_studies.append(study)

    # Sort by Score
    scored_studies.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    # Return Top 7
    return scored_studies[:7]

# Test Block
if __name__ == "__main__":
    # Mock data output from Step 3
    mock_extracted = [
        {
            "id": "111", 
            "study_type": "RCT", 
            "mean_age": 22, 
            "n": 30, 
            "title": "Creatine effects on sprint power",
            "outcome_summary": "Improved athletic performance"
        },
        {
            "id": "222", 
            "study_type": "RCT", 
            "mean_age": 25, 
            "n": 40, 
            "title": "Creatine and memory function",
            "outcome_summary": "Improved cognitive recall"
        },
        {
            "id": "333", 
            "study_type": "Meta-Analysis", 
            "mean_age": 25, 
            "n": 2000, 
            "title": "General safety of creatine",
            "outcome_summary": "No side effects found"
        }
    ]
    
    user_age = 24
    test_goal = "cognition"
    
    print(f"Testing Scorer for Age: {user_age}, Goal: {test_goal}\n")
    
    ranked = score_studies(mock_extracted, user_age, goal=test_goal)
    
    for i, s in enumerate(ranked):
        print(f"#{i+1} [Score: {s['relevance_score']}] ID: {s['id']}")
        print(f"   Reasons: {s['scoring_reasons']}")
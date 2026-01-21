import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

"""
Step 2 - Selector:
1. Selects the top 7 relevant studies.
2. Extracts metadata (study_type, n) for those winners.
3. Merges metadata with the original full abstract.
"""
def select_best_studies(raw_studies, user_age, goal="general"):
    
    if not raw_studies:
        return []

    print(f"DEBUG: Curator analyzing {len(raw_studies)} studies for Age {user_age}, Goal: {goal}...")

    # 1. Prepare Input
    # ID, Title, and Abstract (truncated)
    candidates = []
    for s in raw_studies:
        candidates.append({
            "id": s["id"],
            "title": s["title"],
            "abstract_snippet": s["abstract"][:2500] 
        })

    # 2. Curator Prompt
    system_prompt = f"""
    You are a Senior Medical Research Curator.
    Your Task: Select the top 7 most relevant clinical studies for a user aged {user_age} interested in "{goal}".
    
    CANDIDATE POOL: You have {len(raw_studies)} raw search results.
    
    SELECTION GUIDELINES:
    1. **Strict Relevance:** Discard studies not about the target supplement.
    2. **Age Priority:** Prioritize studies matching age {user_age}.
    3. **Diversity:** Choose a mix of efficacy, safety, and mechanism studies.
    4. **Quality:** Prioritize Meta-Analyses and RCTs.

    OUTPUT FORMAT:
    Return a JSON object with a key "selected_studies" containing a LIST of objects.
    Each object must have:
    - "id": (String) The study ID.
    - "study_type": (String) "RCT", "Meta-Analysis", "Review", "Observational", or "Other".
    - "n": (Int or null) Sample size.
    - "reason": (String) Short reason why you selected this.
    
    Example:
    {{
      "selected_studies": [
        {{ "id": "123", "study_type": "RCT", "n": 45, "reason": "Direct age match" }},
        ...
      ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(candidates)}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1 
        )

        # --- TOKEN DEBUGGING ---
        usage = response.usage
        print(f"DEBUG [Selector]: Input: {usage.prompt_tokens} | Output: {usage.completion_tokens}")
        # -----------------------

        # 3. Parse Choices
        raw_json = response.choices[0].message.content
        parsed = json.loads(raw_json)
        selected_list = parsed.get("selected_studies", [])

        # 4. Combine the LLM's metadata (study_type, n) with the Original (abstract, title)
        
        final_selection = []
        original_map = {s["id"]: s for s in raw_studies}
        
        for item in selected_list:
            pid = item.get("id")
            if pid in original_map:
                original = original_map[pid]
                
                # Merge: Original Data + LLM Metadata
                merged = {**original, **item} 
                final_selection.append(merged)

        print(f"DEBUG: Curator selected {len(final_selection)} studies.")
        return final_selection

    except Exception as e:
        print(f"Error in selection: {e}")
        return []
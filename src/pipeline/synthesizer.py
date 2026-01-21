import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define where the templates live
PROMPT_DIR = os.path.join(os.path.dirname(__file__), "prompts")

"""
Tries to load 'prompts/{goal}.txt'. 
Defaults to 'prompts/general.txt' if not found.
"""
def load_prompt_template(goal):

    filename = f"{goal}.txt"
    filepath = os.path.join(PROMPT_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"DEBUG: Goal '{goal}' not found. Using default.")
        filepath = os.path.join(PROMPT_DIR, "general.txt")
        
    with open(filepath, "r") as f:
        return f.read()

"""
Step 3 - The Writer LLM:
Supports Dynamic Goals (Current: General, Strength, Cognition)
"""
def synthesize_report(supplement, user_age, ranked_studies, goal="general"):

    if not ranked_studies:
        return None

    print(f"DEBUG: Synthesizing '{goal}' report for {supplement}...")

    # 1. Build Study Context
    context_text = ""
    print(f"\nDEBUG: SYNTHESIZER CONTEXT CHECK")
    for study in ranked_studies:
        print(f" - Feeding Study: {study['id']} | Title: {study['title']}...")

        raw_abstract = study.get('abstract', 'No abstract available.')
        
        context_text += f"""
        [Study ID: {study['id']}]
        Title: {study['title']}
        Type: {study['study_type']} (n={study.get('n')})
        
        --- ABSTRACT START ---
        {raw_abstract}
        --- ABSTRACT END ---
        ---------------------
        """

    # 2. Load the external template
    raw_template = load_prompt_template(goal)

    # 3. Fill in template variables
    try:
        system_prompt = raw_template.format(
            user_age=user_age, 
            supplement=supplement
        )
    except KeyError as e:
        print(f"Template Error: Missing placeholder {e}")
        return None

    # 4. Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context_text}"}
            ],
            response_format={ "type": "json_object" },
            temperature=0.2
        )

        # --- TOKEN DEBUGGING ---
        usage = response.usage
        print(f"DEBUG [Synthesizer]: Input Tokens: {usage.prompt_tokens} | Output Tokens: {usage.completion_tokens} | Total: {usage.total_tokens}")
        # -----------------------

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print(f"Error in synthesis: {e}")
        return None

# Test Block
if __name__ == "__main__":
    mock_ranked = [
        {
            "id": "111", "title": "Creatine in Soccer", "study_type": "RCT", 
            "outcome_summary": "Improved sprint power.", "n": 30
        },
        {
            "id": "333", "title": "Creatine Memory", "study_type": "RCT", 
            "outcome_summary": "Improved short term memory.", "n": 50
        }
    ]
    
    print("--- TEST 1: GENERAL ---")
    report = synthesize_report("Creatine", 24, mock_ranked, goal="general")
    # should show "Efficacy & Benefits"
    print(report["summary"][0]["topic"]) 

    print("\n--- TEST 2: STRENGTH ---")
    report = synthesize_report("Creatine", 24, mock_ranked, goal="strength")
    # should show "Muscle & Hypertrophy"
    print(report["summary"][0]["topic"])
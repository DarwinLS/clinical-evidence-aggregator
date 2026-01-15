import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

"""
    Step 3 - Worker LLM:
    Takes raw studies, extracts metadata, AND preserves original title/abstract
    """
def extract_metadata(studies):

    if not studies:
        return []

    print(f"DEBUG: Extracting metadata for {len(studies)} studies...")

    # 1. Prepare input for LLM (truncate to save tokens)
    studies_input = [
        {
            "id": s["id"], 
            "title": s["title"], 
            "abstract": s["abstract"][:2000] 
        } 
        for s in studies
    ]

    # 2. System Prompt
    system_prompt = """
    You are a clinical data extraction engine. You will receive a JSON list of clinical abstracts.
    For EACH abstract, return a structured JSON object with these exact keys:
    
    - id: (The same ID provided in input)
    - study_type: "RCT", "Meta-Analysis", "Systematic Review", "Observational", or "Other"
    - min_age: (Int or null) - ONLY if explicitly stated (e.g. "aged 18-35"). Do NOT infer from mean.
    - max_age: (Int or null) - ONLY if explicitly stated.
    - mean_age: (Int or null) - Extract if stated directly or as "mean +/- SD"
    - n: (Int or null) - The sample size
    - sex: "Male", "Female", "Both", or "Unspecified"
    - outcome_summary: (String, max 15 words) - Key finding regarding the supplement
    
    Output format: A JSON object containing a key "extracted_studies" which is the list of objects.
    Do not guess. If data is missing, use null.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(studies_input)}
            ],
            response_format={ "type": "json_object" }, 
            temperature=0 
        )

        # --- TOKEN DEBUGGING ---
        usage = response.usage
        print(f"DEBUG [Extractor]: Input Tokens: {usage.prompt_tokens} | Output Tokens: {usage.completion_tokens} | Total: {usage.total_tokens}")
        # -----------------------

        # 3. Parse LLM Output
        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        extracted_list = parsed_data.get("extracted_studies", [])

        # LLM output doesn't have the title, add it back
        # Create a lookup dictionary for the original studies
        original_lookup = {s["id"]: s for s in studies}
        
        final_studies = []
        for item in extracted_list:
            original = original_lookup.get(item["id"])
            if original:
                # Merge the LLM data (item) into the original data (original)
                # ensures 'title' and 'abstract' are preserved
                merged = {**original, **item} 
                final_studies.append(merged)
        
        return final_studies

    except Exception as e:
        print(f"Error in extraction: {e}")
        return []

# Test Block
if __name__ == "__main__":
    # Mock data with a Title
    mock_studies = [
        {
            "id": "111",
            "title": "Creatine supplementation in young soccer players",
            "abstract": "Methods: 30 male soccer players (mean age 22) were randomized."
        }
    ]
    
    print("Testing Extractor...")
    results = extract_metadata(mock_studies)
    
    # Check if Title survived
    if results and "title" in results[0]:
        print("SUCCESS: Title was preserved!")
        print(results[0]["title"])
    else:
        print("FAILURE: Title is missing.")
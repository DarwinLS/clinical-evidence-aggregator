import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_metadata(studies):
    """
    Step 3: The Worker LLM.
    Takes a list of raw study dictionaries.
    Returns a list of structured JSON objects with Age, N, and Design.
    """
    if not studies:
        return []

    print(f"DEBUG: Extracting metadata for {len(studies)} studies...")

    # Prepare the input as a clean JSON string to save tokens
    studies_input = [
        {
            "id": s["id"], 
            "title": s["title"], 
            "abstract": s["abstract"][:2000] # Truncate massive abstracts to save costs
        } 
        for s in studies
    ]

    # System Prompt: strict instructions on how to extract data
    system_prompt = """
    You are a clinical data extraction engine. You will receive a JSON list of clinical abstracts.
    For EACH abstract, return a structured JSON object with these exact keys:
    
    - id: (The same ID provided in input)
    - study_type: "RCT", "Meta-Analysis", "Systematic Review", "Observational", or "Other"
    - min_age: (Int or null)
    - max_age: (Int or null)
    - mean_age: (Int or null) - Infer if mentioned like "mean age 24 +/- 2"
    - n: (Int or null) - The sample size
    - sex: "Male", "Female", "Both", or "Unspecified"
    - outcome_summary: (String, max 15 words) - Key finding regarding the supplement
    
    Output format: A JSON object containing a key "extracted_studies" which is the list of objects.
    Do not guess. If data is missing, use null.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # current optimal cheap/fast model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(studies_input)}
            ],
            response_format={ "type": "json_object" }, # Crucial: Forces valid JSON
            temperature=0 # Crucial: Makes the model deterministic
        )

        # Parse result
        raw_json = response.choices[0].message.content
        parsed_data = json.loads(raw_json)
        
        return parsed_data.get("extracted_studies", [])

    except Exception as e:
        print(f"Error in extraction: {e}")
        return []

# Test Block
if __name__ == "__main__":
    # Mock data to test ONLY this file without hitting PubMed
    mock_studies = [
        {
            "id": "111",
            "title": "Creatine supplementation in young soccer players",
            "abstract": "Methods: 30 male soccer players (mean age 22) were randomized. Results: Power output increased."
        },
        {
            "id": "222",
            "title": "Effects of creatine in the elderly",
            "abstract": "We studied 50 women aged 60-75. No significant changes were found in muscle mass."
        }
    ]
    
    print("Testing Extractor...")
    results = extract_metadata(mock_studies)
    print(json.dumps(results, indent=2))
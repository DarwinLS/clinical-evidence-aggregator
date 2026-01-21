from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import logging

# IMPORT PIPELINE MODULES
from src.services.pubmed import search_pubmed
from src.pipeline.selector import select_best_studies
from src.pipeline.synthesizer import synthesize_report

# Configure logging so you can see what's happening in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Pass defaults to avoid Jinja2 errors on initial load
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "result": None,
        "search_term": "",
        "search_age": "",
        "search_goal": "general"
    })

@app.post("/analyze", response_class=HTMLResponse)
async def analyze_supplement(
    request: Request, 
    supplement: str = Form(...), 
    age: int = Form(...),
    goal: str = Form("general")
):
    logger.info(f"--- STARTING PIPELINE for {supplement} (Age {age}, Goal: {goal}) ---")
    
    # 1. FETCH
    raw_studies = search_pubmed(supplement, max_results=20)
    
    if raw_studies is None: 
         return render_error(request, "No studies found.", supplement, age, goal)

    # 2. CURATE
    top_studies = select_best_studies(raw_studies, user_age=age, goal=goal)

    if not top_studies:
        return render_error(request, "No relevant studies found after curation.", supplement, age, goal)

    # 4. SYNTHESIZE
    final_report = synthesize_report(supplement, age, top_studies, goal=goal)
    
    if not final_report:
        return render_error(request, "Failed to generate summary.", supplement, age, goal)

    # SANITIZE CITATIONS
    study_lookup = {s['id']: s for s in top_studies}
    bibliography = []
    citation_map = {}
    citation_counter = 1

    if final_report and "summary" in final_report:
        for section in final_report["summary"]:
            clean_ids = []
            raw_ids = section.get("citation_ids", [])
            
            if isinstance(raw_ids, str):
                raw_ids = [raw_ids]
            
            for raw_id in raw_ids:
                str_id = str(raw_id)
                if str_id in study_lookup:
                    clean_ids.append(str_id)
                    if str_id not in citation_map:
                        citation_map[str_id] = citation_counter
                        citation_map[str_id] = citation_counter
                        bibliography.append(study_lookup[str_id])
                        citation_counter += 1
            
            section["citation_ids"] = clean_ids

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "result": final_report,
        "bibliography": bibliography,
        "citation_map": citation_map,
        "study_lookup": study_lookup,
        "search_term": supplement,
        "search_age": age,
        "search_goal": goal
    })

def render_error(request, message, supplement="", age="", goal=""):
    """Helper to show error messages on the frontend"""
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "error": message,
        "search_term": supplement,
        "search_age": age,
        "search_goal": goal
    })

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
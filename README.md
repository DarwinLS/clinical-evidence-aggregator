# Clinical Evidence Aggregator (MVP)

A research engine that builds evidence-based reports on supplements by aggregating live clinical data.

Unlike generic chatbots that hallucinate citations, this system retrieves raw clinical abstracts from PubMed, filters them using a **Curator LLM** based on user demographics and goals, and synthesizing a structured report where every claim is strictly tied to a source ID.

> **Status:** MVP (Deployed on Render)
> **Stack:** Python, FastAPI, OpenAI (GPT-4o), PubMed API

---

## ⚡ The Problem vs. The Solution

**The Problem:** If you ask ChatGPT "Does Beta Alanine work?", it relies on training data (which is old/generic) and often hallucinates studies or ignores your specific context (e.g., age or specific fitness goal).

**Our Solution:** A "RAG-style" pipeline that:
1.  **Fetches Fresh Data:** Hits the PubMed API in real-time.
2.  **Curates Semantically:** Uses an LLM to read abstracts and pick the *best* 7 studies for your specific age and goal (e.g., "Cognition" vs "Hypertrophy").
3.  **Synthesizes with "Lazy Evaluation":** Feeds the *full* text of only the winning studies to a Writer LLM for high-fidelity extraction of dosage and safety protocols.

---

## 🏗️ Architecture & Pipeline

The application logic has moved away from rigid regex scoring to a **semantic curation pipeline**:

### 1. The Search (PubMed API)
* **Input:** Supplement + User Age.
* **Query:** Executes a boolean search strictly for `"{Supplement}"[Title/Abstract]` to avoid partial matches (e.g., preventing "Beta-Blockers" when searching "Beta Alanine").
* **Filters:** Restricts to Meta-Analyses, Systematic Reviews, Clinical Trials, and RCTs.

### 2. The Curator (`src/pipeline/selector.py`)
* **Model:** `gpt-4o-mini` (Fast/Cost-effective).
* **Task:** Receives 20-30 raw abstracts. It acts as a semantic filter to:
    * Discard irrelevant noise (e.g., "Heart Valve" studies for "Beta Alanine").
    * Prioritize user age relevance and goal.
    * **Enforce Diversity:** Explicitly selects a mix of efficacy, safety, and mechanism papers so the final report isn't one-dimensional.
* **Output:** Returns the top 7 "Winner" studies with cleaned metadata (`n`, `study_type`).

### 3. The Synthesizer (`src/pipeline/synthesizer.py`)
* **Model:** `gpt-4o` (High-fidelity).
* **Strategy:** "Lazy Evaluation." It receives the **Full Raw Abstracts** of the 7 winners.
* **Prompting:** Uses dynamic prompt templates (`prompts/strength.txt`, `prompts/cognition.txt`) to structure the report.
* **Constraint:** Zero-shot citation. It must cite specific Study IDs for every claim. If data is missing in the text, it must explicitly state "Insufficient data."

### 4. The Frontend
* **Rendering:** Jinja2 templates render the structured JSON.
* **Citations:** citations are sanitized server-side. The frontend displays academic superscripts `[1]` that link to a generated bibliography with direct PubMed links.

---

## 🚀 Features

* **Goal-Aware Reports:** Searching "Creatine" with the goal **"Cognition"** generates a completely different report (focusing on memory/depression) than the goal **"Strength"** (focusing on hypertrophy).
* **Strict Citation System:** Citations are not hallucinations. They are mapped to the actual PubMed IDs retrieved in Step 1.
* **Token Optimization:** We use a cheaper model (`mini`) to filter bulk noise and a smarter model (`4o`) only for the final synthesis, keeping costs minimal while maintaining accuracy.
* **Safety First:** A dedicated "Safety & Side Effects" section is mandatory in every report, forced by the prompt structure.

---

## 🛠️ Local Setup

### Prerequisites
* Python 3.10+
* OpenAI API Key

### Installation

1.  **Clone the repo**
    ```bash
    git clone [https://github.com/yourusername/clinical-aggregator.git](https://github.com/yourusername/clinical-aggregator.git)
    cd clinical-aggregator
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**
    Create a `.env` file in the root:
    ```ini
    OPENAI_API_KEY=sk-proj-your-key-here
    EMAIL=your-email@example.com  # Required for PubMed API politeness
    ```

### Running the App

```bash
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000` in your browser.

---

## 📦 Deployment (Render)

This MVP is configured for **Render** Web Services.

1.  **Build Command:** `pip install -r requirements.txt`
2.  **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
3.  **Environment Variables:** `OPENAI_API_KEY` and `EMAIL` in the Render dashboard.

---

## 📝 Directory Structure

```text
/
├── main.py                 # FastAPI entry point & Orchestrator
├── requirements.txt        # Dependencies
├── static/
│   ├── style.css           # UI Styling
│   └── script.js           # Modal logic
├── templates/
│   └── index.html          # Jinja2 Frontend Template
└── src/
    ├── services/
    │   └── pubmed.py       # PubMed API Handler
    └── pipeline/
        ├── selector.py     # The "Curator" (LLM Filter)
        ├── synthesizer.py  # The "Writer" (LLM Report Generator)
        └── prompts/        # Dynamic Text Prompts
            ├── general.txt
            ├── strength.txt
            └── cognition.txt
```

## 🔮 Future Roadmap

The current MVP proves the "Curator-Synthesizer" architecture works. The next phase focuses on personalization fidelity.

### High Priority
* ** Biological Sex Filtering:** Currently, the system assumes a generic physiological baseline. We will add a `sex` parameter to the Curator to prioritize studies matching the user's biological sex (e.g., filtering out or reducing priority of male-only hypertrophy studies for female users).
* ** Full-Text Retrieval:** Move beyond abstracts. Integration with PMC (PubMed Central) API to parse full PDF methodology sections for granular protocol extraction.

### Long Term
* ** User Profiles:** Save "Watchlists" for specific supplements.
* ** New Study Alerts:** Auto-run the Curator once a week and email users if a new "Winner" study is published in their age group.

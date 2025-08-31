# Social Support Application Agent

A modular AI-powered system for public-sector social support casework.  
It ingests applicant documents, validates and featurizes data, predicts eligibility, synthesizes enablement recommendations and a human-readable summary, stores results in Qdrant, and exposes a RAG chatbot over the generated reports.

**Default ports**
- **API (FastAPI)**: http://localhost:8000  
- **Streamlit UI**: http://localhost:3000  
- **Qdrant (REST)**: http://localhost:6333 (gRPC: 6334)

---

## Features

- **Document ingestion & extraction** (assets/liabilities XLSX, bank CSV, credit PDF, Emirates ID image)
- **Validation** & data quality scoring (confidence, high-severity checks)
- **Eligibility prediction** (scikit-learn classifier)
- **Decisioning** (APPROVE / REVIEW / SOFT_DECLINE) with reasons
- **Enablement plan** synthesis (LLM) tailored to the applicant
- **Final summary** synthesis (LLM) for the UI and reports
- **Vector storage** (Qdrant) + rich text payload for semantic search
- **RAG chatbot** over generated TXT reports (`reports/`)
- **FastAPI** service + **Streamlit** UI

---

## Project Structure

```
Social Support Application Agent/
├── README.md
├── requirements.txt
├── data_syntethizer.py
├── eligibility_model.pkl
├── process_application.py
├── Dockerfile
├── docker-compose.yml
├── synthetic_data/
│   ├── assets_liabilities/
│   ├── bank_statements/
│   ├── credit_reports/
│   ├── emirates_ids/
│   └── test_data/
├── api/
│   ├── __init__.py
│   ├── chatbot.py
│   └── server.py
├── database/
│   ├── __init__.py
│   └── qdrant_client.py
├── file_processor/
│   ├── __init__.py
│   ├── assets_liabilities_processor.py
│   ├── bank_statement_processor.py
│   ├── credit_report_processor.py
│   ├── emirates_id_processor.py
│   └── file_processor.py
├── model_training/
│   ├── __init__.py
│   ├── eligibility_classifier.py
│   ├── test_classifier.py
│   └── train_eligibility_classifier.py
├── orchestration/
│   ├── __init__.py
│   ├── graph.py
│   ├── state.py
│   └── nodes/
│       ├── build_features.py
│       ├── decide_and_recommend.py
│       ├── ingest_extract.py
│       ├── score_eligibility.py
│       ├── summarize_for_ui.py
│       ├── validate_consistency.py
│       └── vector_store_and_similar.py
├── utils/
│   ├── __init__.py
│   └── ollama_utils.py
```
---

## What You Get

- **FastAPI** service (`/process`, `/chat`)
- **Streamlit** UI (file intake + chatbot)
- **LangGraph** orchestration (ingest → validate → features → score → decide → enablement → summarize → store)
- **Qdrant** vector storage to store applicants data
- **LlamaIndex** RAG over `reports/`
- **Ollama**-backed generation (enablement, summaries, comprehensive reports)

---

## Prerequisites

- **Python** 3.11+
- **Docker** & **Docker Compose**
- **Ollama** (local LLM runtime): https://ollama.com (install & run `ollama serve`)
- **Qdrant** (runs via Docker in this guide)

> If `requirements.txt` doesn’t include these, add them:
> ```
> fastapi uvicorn[standard] streamlit
> langgraph langchain pydantic
> pandas numpy scikit-learn joblib PyPDF2 requests
> llama-index-core llama-index-llms-ollama llama-index-embeddings-ollama
> qdrant-client
> ```

---

## Quick Start (Docker Compose)

This is the easiest way to run everything.

1) **Start all services**
```bash
docker compose up --build
```
2) **Change the base url in on the frontend's API Settings to:**
```bash
http://api:8000
```
## Open:

* Streamlit UI → http://localhost:3000

* API (docs) → http://localhost:8000/docs

* Qdrant REST → http://localhost:6333

* The Streamlit UI’s sidebar “API Base URL” should be http://api:8000

---

## Manual Setup

### 1) Create & Activate Virtual Environment

#### macOS/Linux:
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows (PowerShell):
```bash
python -m venv myenv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Install & Start Ollama, Pull Models
Install from https://ollama.com, then:
```bash
# start daemon (if not already running)
ollama serve

# pull models used by this project
ollama pull qwen2.5vl:3b
ollama pull all-minilm:latest
```

### 3) Start Qdrant (Container)
```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v qdrant_storage:/qdrant/storage \
  qdrant/qdrant:latest
```

### 4) Train/Ensure Eligibility Model (once)
If you don’t already have `eligibility_model.pkl`:
```bash
python model_training/train_eligibility_classifier.py
```

### 5) Start the FastAPI Server
```bash
export QDRANT_HOST="localhost"
export QDRANT_PORT="6333"
# optional: OLLAMA_BASE_URL="http://localhost:11434"

uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

#### CORS (if needed) – allow the Streamlit origin to call the API:

Add in `api/server.py` after `app = FastAPI(...)`:
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 6) Start the Streamlit UI (port 3000)
```bash
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 3000
```

Open [http://localhost:3000](http://localhost:3000) and set API Base URL to `http://localhost:8000` in the sidebar.

---

## Using the App

### A) Intake & Decision

In the left panel, upload exactly four files:

- **Assets & Liabilities:** `.xlsx` / `.xls`
- **Bank Statement:** `.csv`
- **Credit Report:** `.pdf`
- **Emirates ID:** `.png` / `.jpg` / `.jpeg`

Click **Process Application**.

The UI shows:

- **Decision Status** (from `decision.status`)
- **Final Summary** (LLM-synthesized)

**Sample `/process` response:**
```json
{
  "decision": {
    "status": "SOFT_DECLINE",
    "reasons": [{ "text": "Low eligibility score (0.00) or model predicted ineligible" }],
    "score": 0,
    "confidence": 1
  },
  "final_summary": "Angela Gibbs, with a monthly income of AED 17,116.0, is single and employed... (truncated)"
}
```

During processing the system also creates a comprehensive TXT report per applicant under `reports/` and stores a rich payload + embedding in Qdrant. The chatbot uses these reports for RAG.

### B) Chatbot (RAG over `reports/`)

Use the chat on the right to ask questions grounded in generated reports.

Backend endpoint: `POST /chat` with `{"message":"...", "directory":"reports"}`.

---

## API Endpoints

- **POST `/process`** — multipart upload (`files[]`), triggers full workflow; returns only:
  - `decision` (status, reasons, score, confidence)
  - `final_summary` (string)

- **POST `/chat`** — body: `{"message": "...", "directory": "reports"}`; returns:
  - `answer` (string)

- **GET `/`** — health

---


---

## Synthetic Data & Model

**Generate synthetic data:**
```bash
python data_syntethizer.py
```

**Train eligibility model:**
```bash
python model_training/train_eligibility_classifier.py
```

---

## Troubleshooting

- **Streamlit can’t call API (CORS):**  
  Add the CORS middleware snippet in `api/server.py` (see above).

- **No RAG answers:**  
  Ensure `reports/` contains TXT reports (process at least one applicant first).

- **Qdrant connection errors:**  
  Confirm container is up and env vars `QDRANT_HOST`/`QDRANT_PORT` are set correctly.

- **Ollama not reachable:**  
  Verify `ollama serve` is running and `OLLAMA_BASE_URL` points to it; confirm models pulled.

- **Port in use:**  
  Change ports or stop existing processes (`lsof -i :3000`, `lsof -i :8000`, etc.).

---

## Extending & Customizing

- **Add new document processors:**  
  Add files in `file_processor/`

- **Adjust validation thresholds:**  
  Edit `orchestration/nodes/validate_consistency.py`

- **Tune decision policy & enablement prompts:**  
  Edit `orchestration/nodes/decide_and_recommend.py`

- **Modify final summary synthesis:**  
  Edit `orchestration/nodes/summarize_for_ui.py`

- **Enrich Qdrant payload/schema:**  
  Edit `database/qdrant_client.py`



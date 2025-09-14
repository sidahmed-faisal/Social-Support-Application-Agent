# api/server.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import tempfile, os, shutil
from pydantic import BaseModel
from typing import Optional

from orchestration.graph import build_graph
from .chatbot import rag_answer

app = FastAPI(title="Social Support AI Orchestrator")

graph_app = build_graph()


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/process")
async def process(files: List[UploadFile] = File(...)):
    """
    Accepts multiple files (CSV/XLSX/PDF/PNG/JPG/JPEG) via multipart/form-data,
    runs the LangGraph workflow, and returns ONLY:
      - decision
      - final_summary
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    tmp_dir = tempfile.mkdtemp(prefix="ssa_upload_")
    saved_paths: List[str] = []

    try:
        # Persist uploads to disk so existing processors can read by path
        for f in files:
            _, ext = os.path.splitext(f.filename or "")
            ext = ext.lower()
            if ext not in [".csv", ".xlsx", ".pdf", ".png", ".jpg", ".jpeg"]:
                raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

            dest = os.path.join(tmp_dir, f.filename)
            with open(dest, "wb") as out:
                out.write(await f.read())
            saved_paths.append(dest)

        # Run the orchestration graph
        init_state = {"file_paths": saved_paths}
        result = graph_app.invoke(init_state)

        decision = result.get("decision").get("status").replace("_", " ") if result.get("decision") else None
        final_summary = result.get("final_summary")
        validated_data = result.get("validated", {})
        
        # Extract inconsistencies from validated data if present
        inconsistencies = validated_data.get("_inconsistencies", [])


        if decision is None or final_summary is None:
            raise HTTPException(
                status_code=500,
                detail="Workflow did not produce decision and/or final_summary."
            )

        return {
            "decision": decision,
            "final_summary": final_summary,
            "result": result,
            "inconsistencies": inconsistencies

        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass



class ChatRequest(BaseModel):
    message: str
    directory: Optional[str] = "reports"

@app.post("/chat")
def chat_rag(req: ChatRequest):
    """
    Run a RAG chat over the documents in `req.directory` (default: 'reports').
    Returns a single field:
      - answer: string
    """
    try:
        answer = rag_answer(message=req.message, directory=req.directory)
        return {"answer": answer}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

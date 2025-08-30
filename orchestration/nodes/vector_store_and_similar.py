# orchestration/nodes/vector_store_and_similar.py
import datetime
from typing import Dict, Any, List
import os, re

# Ollama embeddings
try:
    from utils.ollama_utils import OllamaClient
except Exception:  # pragma: no cover
    from ollama_utils import OllamaClient  # fallback

# Qdrant storage client
QDRANT_AVAILABLE = True
try:
    from database.qdrant_client import QdrantStorage
except Exception:
    QDRANT_AVAILABLE = False



class _InMemoryStore:
    def __init__(self):
        self._data = []
    def store_applicant(self, payload: Dict[str, Any], embedding: List[float]):
        self._data.append({"payload": payload, "embedding": embedding})
        return str(len(self._data))
    def search_similar_applicants(self, embedding: List[float], limit: int = 3):
        return []

_mem_store = _InMemoryStore()

def _normalize_eid(eid_val: Any) -> str:
    """Normalize emirates_id from different shapes."""
    if isinstance(eid_val, dict):
        return str(eid_val.get("emirates_id") or "").strip()
    return str(eid_val or "").strip()

def _build_text_content_from_payload(payload: Dict[str, Any]) -> str:
    # If QdrantStorage is available, reuse its comprehensive text builder
    try:
        if QDRANT_AVAILABLE:
            helper = QdrantStorage()
            return helper._create_text_content(payload)  # type: ignore[attr-defined]
    except Exception:
        pass

    # Fallback: a rich-enough text blob
    decision = payload.get("decision", {}) or {}
    enablement = payload.get("enablment_and_recommendations", {}) or {}
    lines = [
        f"Applicant: {payload.get('name', 'Unknown')}",
        f"Emirates ID: {payload.get('emirates_id', 'Unknown')}",
        f"Monthly Income: {payload.get('monthly_income', 0)}",
        f"Family Size: {payload.get('family_size', 1)}",
        f"Employment Status: {payload.get('employment_status', 'Unknown')}",
        f"Housing Type: {payload.get('housing_type', 'Unknown')}",
        f"Marital Status: {payload.get('marital_status', 'Unknown')}",
        f"Has Disability: {payload.get('has_disability', False)}",
        f"Nationality: {payload.get('nationality', 'Unknown')}",
        f"Credit Score: {payload.get('credit_score', 650)}",
        f"Net Worth: {payload.get('net_worth', 0)}",
        f"Eligibility Score: {payload.get('eligibility_score', 0)}",
        f"Eligibility Prediction: {payload.get('eligibility_prediction', 0)}",
        f"Decision Status: {decision.get('status', 'Unknown')}",
    ]
    app_summary = enablement.get("applicant_summary") or ""
    if app_summary:
        lines.append(f"Applicant Summary: {app_summary}")
    recs = enablement.get("recommendations") or []
    for i, rec in enumerate(recs[:5]):
        lines.append(f"Recommendation {i+1}: type={rec.get('type','')}; rationale={rec.get('rationale','')}; actions={', '.join(rec.get('suggested_actions', []))}")
    return "\n".join(lines)


def _normalize_eid(eid_val: Any) -> str:
    """Normalize emirates_id from different shapes."""
    if isinstance(eid_val, dict):
        return str(eid_val.get("emirates_id") or "").strip()
    return str(eid_val or "").strip()

def _project_root_dir() -> str:
    # this file: orchestration/nodes/vector_store_and_similar.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _safe_filename(s: str) -> str:
    s = s.strip() or "applicant"
    s = re.sub(r"[^\w\-]+", "_", s)
    return s[:100]

def _build_report_prompt(payload: Dict[str, Any]) -> str:
    """Build a comprehensive-report prompt from the stored payload (includes decision + enablement)."""
    # Identity & core signals
    identity = (
        f"Name: {payload.get('name','Unknown')}\n"
        f"Emirates ID: {payload.get('emirates_id','Unknown')}\n"
        f"Nationality: {payload.get('nationality','Unknown')}\n"
    )
    financial = (
        f"Monthly Income (AED): {payload.get('monthly_income',0)}\n"
        f"Family Size: {payload.get('family_size',1)}\n"
        f"Employment Status: {payload.get('employment_status','Unknown')}\n"
        f"Housing Type: {payload.get('housing_type','Unknown')}\n"
        f"Marital Status: {payload.get('marital_status','Unknown')}\n"
        f"Has Disability: {payload.get('has_disability',False)}\n"
        f"Credit Score: {payload.get('credit_score',650)}\n"
        f"Net Worth (AED): {payload.get('net_worth',0)}\n"
    )
    # Decision
    decision = payload.get("decision", {}) or {}
    reasons_list = decision.get("reasons") or []
    reasons_text = "; ".join(
        (r.get("text","") if isinstance(r, dict) else str(r)).strip()
        for r in reasons_list if r
    ) or "N/A"
    decision_block = (
        f"Decision Status: {decision.get('status','REVIEW')}\n"
        f"Eligibility Score: {payload.get('eligibility_score',0):.2f}\n"
        f"Validation Confidence: {decision.get('confidence',0):.2f}\n"
        f"Decision Reasons: {reasons_text}\n"
    )
    # Enablement
    en = payload.get("enablment_and_recommendations", {}) or {}
    app_summary = en.get("applicant_summary","").strip()
    recs = en.get("recommendations") or []
    rec_lines = []
    for i, rec in enumerate(recs[:5], start=1):
        rtype = rec.get("type","other")
        rationale = (rec.get("rationale") or "").strip()
        actions = rec.get("suggested_actions") or []
        actions_str = "; ".join(map(str, actions[:3])) if actions else "N/A"
        rec_lines.append(f"{i}. {rtype} — {rationale}\n   Actions: {actions_str}")
    recs_block = "\n".join(rec_lines) if rec_lines else "None"

    return (
        "You are a public-sector caseworker assistant. Draft a comprehensive, well-structured report for the applicant.\n"
        "Audience: a government case officer. Tone: clear, factual, and concise.\n"
        "Structure the report with these sections (use headings):\n"
        "1) Applicant Identity\n"
        "2) Financial & Household Profile\n"
        "3) Eligibility Assessment\n"
        "4) Decision & Rationale\n"
        "5) Enablement Plan (types, rationales, and concrete actions)\n\n"
        "Content to use:\n"
        "=== Applicant Identity ===\n" + identity + "\n"
        "=== Financial & Household Profile ===\n" + financial + "\n"
        "=== Eligibility Assessment ===\n"
        f"Eligibility Score: {payload.get('eligibility_score',0):.2f}\n"
        "Summary of strengths/risks based on the signals above.\n\n"
        "=== Decision & Rationale ===\n" + decision_block + "\n"
        "=== Enablement Plan ===\n"
        f"Applicant Summary: {app_summary or 'N/A'}\n"
        "Recommendations:\n" + recs_block + "\n\n"
        "Return ONLY a JSON object with this schema:\n"
        "{\n"
        '  "report": "string (multi-line comprehensive report)"\n'
        "}\n"
        "Think step-by-step but output only valid JSON."
    )

def _synthesize_report_text(ollama: OllamaClient, payload: Dict[str, Any]) -> str:
    prompt = _build_report_prompt(payload)
    schema = {"report": "string"}
    result = ollama.structured_extraction(prompt, schema) or {}
    report_text = ""
    if isinstance(result, dict):
        report_text = str(result.get("report") or "").strip()
    # Fallback: assemble a minimal narrative if LLM fails
    if not report_text:
        fallback = [
            "# Applicant Identity",
            f"Name: {payload.get('name','Unknown')} | EID: {payload.get('emirates_id','Unknown')} | Nationality: {payload.get('nationality','Unknown')}",
            "",
            "# Financial & Household Profile",
            f"Income: {payload.get('monthly_income',0)} AED | Family: {payload.get('family_size',1)} | Employment: {payload.get('employment_status','Unknown')} | Housing: {payload.get('housing_type','Unknown')} | Marital: {payload.get('marital_status','Unknown')} | Disability: {payload.get('has_disability',False)} | Credit: {payload.get('credit_score',650)} | Net Worth: {payload.get('net_worth',0)}",
            "",
            "# Eligibility Assessment",
            f"Eligibility Score: {payload.get('eligibility_score',0):.2f}",
            "",
            "# Decision & Rationale",
            f"Decision: {payload.get('decision',{}).get('status','REVIEW')}",
        ]
        reasons = payload.get("decision",{}).get("reasons") or []
        if reasons:
            reasons_text = "; ".join((r.get('text','') if isinstance(r,dict) else str(r)).strip() for r in reasons if r)
            if reasons_text:
                fallback.append(f"Reasons: {reasons_text}")
        en = payload.get("enablment_and_recommendations", {}) or {}
        fallback.append("")
        fallback.append("# Enablement Plan")
        if en.get("applicant_summary"):
            fallback.append(f"Summary: {en['applicant_summary']}")
        recs = en.get("recommendations") or []
        for i, rec in enumerate(recs[:5], start=1):
            rtype = rec.get("type","other")
            rationale = (rec.get("rationale") or "").strip()
            actions = rec.get("suggested_actions") or []
            actions_str = "; ".join(map(str, actions[:3])) if actions else ""
            line = f"{i}. {rtype} — {rationale}"
            if actions_str:
                line += f" | Actions: {actions_str}"
            fallback.append(line)
        report_text = "\n".join(fallback)
    return report_text


def vector_store_and_similar(state: Dict[str, Any]) -> Dict[str, Any]:
    validated = state.get("validated") or {}
    decision = state.get("decision") or {}
    score = float(state.get("eligibility_score", 0.0))
    pred = int(state.get("eligibility_prediction", 0))

    # Enablement + final summary
    enablement_recommendations: List[Dict[str, Any]] = state.get("enablement") or []
    final_summary: str = str(state.get("final_summary") or "").strip()

    eid = _normalize_eid(validated.get("emirates_id"))

    # Condense enablement recommendations to required fields
    condensed_recs = []
    for rec in enablement_recommendations:
        condensed_recs.append({
            "type": rec.get("type"),
            "rationale": rec.get("rationale"),
            "suggested_actions": rec.get("suggested_actions") or []
        })

    # Build full payload
    payload = {
        "applicant_id": eid,
        "name": validated.get("name", "Unknown"),
        "emirates_id": eid,
        "monthly_income": validated.get("monthly_income", 0),
        "family_size": validated.get("family_size", 1),
        "employment_status": validated.get("employment_status", "Unknown"),
        "housing_type": validated.get("housing_type", "Unknown"),
        "marital_status": validated.get("marital_status", "Unknown"),
        "has_disability": validated.get("has_disability", False),
        "nationality": validated.get("nationality", "Unknown"),
        "credit_score": validated.get("credit_score", 650),
        "net_worth": validated.get("net_worth", 0),
        "eligibility_score": score,
        "eligibility_prediction": pred,
        "decision": decision,
        "enablment_and_recommendations": {
            "applicant_summary": final_summary,
            "recommendations": condensed_recs
        }
    }

    # Build the same rich text used for Qdrant and FAISS
    text_content = _build_text_content_from_payload(payload)

    # Generate embedding from text content
    ollama = OllamaClient()
    embedding = ollama.generate_embedding(text_content)
    report_text = _synthesize_report_text(ollama, payload)

    root_dir = _project_root_dir()
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)


    # Use applicant name; sanitize; no timestamp as requested
    applicant_name = payload.get("name") or "applicant"
    name_part = _safe_filename(applicant_name)
    report_filename = f"{name_part}_economic_enablement_report.txt"
    report_path = os.path.join(reports_dir, report_filename)

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
    except Exception as e:
        # Non-fatal: continue even if file write fails
        print(f"Report write error: {e}")

    # --- Qdrant storage ---
    if QDRANT_AVAILABLE:
        try:
            client = QdrantStorage()
            point_id = client.store_applicant({**payload, "text": text_content}, embedding)
            hits = client.search_similar_applicants(embedding, limit=3) or []
            similar = [{"score": getattr(h, "score", None), "payload": getattr(h, "payload", h)} for h in hits]
        except Exception as e:
            print(f"Qdrant storage error: {e}")
            point_id = _mem_store.store_applicant(payload, embedding)
            similar = []
    else:
        point_id = _mem_store.store_applicant(payload, embedding)
        similar = []



    return {
        "embedding": embedding,
        "point_id": point_id,
        "similar_applicants": similar
    }

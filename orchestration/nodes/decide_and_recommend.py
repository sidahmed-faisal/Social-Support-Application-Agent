# orchestration/nodes/decide_and_recommend.py
from typing import Dict, Any, List

# Thresholds
TAU_APPROVE = 0.70
TAU_DECLINE = 0.35
C_MIN = 0.70

# Use your existing Ollama client
try:
    from utils.ollama_utils import OllamaClient
except Exception:  # pragma: no cover
    from ollama_utils import OllamaClient  # fallback


def _reason(text: str) -> Dict[str, Any]:
    return {"text": text}

# --- Rule-based fallback (only used if LLM synthesis fails) ---
def _fallback_enablement(validated: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    income = float(validated.get("monthly_income", 0) or 0)
    employed = (validated.get("employment_status") == "Employed")
    housing = (validated.get("housing_type") or "Unknown")
    credit_score = float(validated.get("credit_score", 650) or 650)
    family = int(validated.get("family_size", 1) or 1)

    if not employed:
        out.append({"type": "job_match", "rationale": "Unemployed or self-employed with low income",
                    "suggested_actions": ["Explore job matching portal", "Enroll in short upskilling course"],
                    "priority": "high"})
    if credit_score < 600:
        out.append({"type": "financial_counseling", "rationale": "Low credit score",
                    "suggested_actions": ["Debt management session", "Budgeting workshop"], "priority": "medium"})
    if housing == "Shared" and family >= 4:
        out.append({"type": "rental_support", "rationale": "Large family in shared housing",
                    "suggested_actions": ["Apply for rental subsidy", "Search larger unit options"], "priority": "high"})
    if income < 8000:
        out.append({"type": "income_support", "rationale": "Low monthly income",
                    "suggested_actions": ["Temporary income support", "Upskilling stipend"], "priority": "high"})
    if not out:
        out.append({"type": "other", "rationale": "No clear gaps detected",
                    "suggested_actions": ["General career counseling"], "priority": "low"})
    return out

# --- LLM-based synthesis of enablement plan ---
def _build_enablement_prompt(validated: Dict[str, Any], decision: Dict[str, Any]) -> str:
    # Include demographic + financial profile in the prompt
    profile_lines = [
        f"Name: {validated.get('name', 'Unknown')}",
        f"Emirates ID: {validated.get('emirates_id', 'Unknown')}",
        f"Monthly Income (AED): {validated.get('monthly_income', 0)}",
        f"Family Size: {validated.get('family_size', 1)}",
        f"Employment Status: {validated.get('employment_status', 'Unknown')}",
        f"Housing Type: {validated.get('housing_type', 'Unknown')}",
        f"Marital Status: {validated.get('marital_status', 'Unknown')}",
        f"Has Disability: {validated.get('has_disability', False)}",
        f"Nationality: {validated.get('nationality', 'Unknown')}",
        f"Credit Score: {validated.get('credit_score', 650)}",
        f"Net Worth (AED): {validated.get('net_worth', 0)}",
    ]
    decision_line = f"Decision Context: status={decision.get('status','REVIEW')}, score={decision.get('score',0):.2f}, confidence={decision.get('confidence',0):.2f}"

    # Building prompt with fallback logic embedded
    return (
        "You are a caseworker assistant. Based on the applicant profile below, "
        "synthesize tailored **economic enablement** recommendations. Focus on actionable, "
        "practical steps within public-sector programs (training, job matching, career counseling, "
        "financial counseling, rental support, income support if salary and  Net Worth are low, disability support). "
        "Be concise and impactful.\n\n"
        "Applicant Profile:\n"
        + "\n".join(profile_lines) + "\n"
        + decision_line + "\n\n"
        "Return ONLY a JSON object matching this schema:\n"
        "{\n"
        '  "overall_summary": "string (2-3 sentences max)",\n'
        '  "enablement_recommendations": [\n'
        "    {\n"
        '      "type": "training|job_match|career_counseling|financial_counseling| income support|rental_support|disability_support|other",\n'
        '      "rationale": "string",\n'
        '      "suggested_actions": ["string", "string", "string"],\n'
        '      "priority": "high|medium|low"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Think step-by-step before producing the final JSON.\n"
        "If there are no clear gaps or issues detected, generate recommendations as follows:\n"
        "- If employment status is 'Employed', suggest career counseling, upskilling, or job matching.\n"
        "- If credit score is below 600, recommend financial counseling.\n"
        "- If housing type is 'Shared' and family size is 4 or more, suggest rental support.\n"
        "If no clear gaps, suggest general career counseling and financial planning support."
    )

def _synthesize_enablement(validated: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
    ollama = OllamaClient()
    prompt = _build_enablement_prompt(validated, decision)
    schema = {
        "overall_summary": "string",
        "enablement_recommendations": [
            {
                "type": "string",
                "rationale": "string",
                "suggested_actions": ["string"],
                "priority": "string"
            }
        ]
    }
    # We reuse structured_extraction to coerce JSON output
    result = ollama.structured_extraction(prompt, schema) or {}
    # Validate minimal shape
    if not isinstance(result, dict) or "enablement_recommendations" not in result:
        return {"overall_summary": "", "enablement_recommendations": _fallback_enablement(validated)}
    recs = result.get("enablement_recommendations") or []
    if not isinstance(recs, list) or not recs:
        result["enablement_recommendations"] = _fallback_enablement(validated)
    return result

def decide_and_recommend(state: Dict[str, Any]) -> Dict[str, Any]:
    validated = state.get("validated") or {}
    score = float(state.get("eligibility_score", 0.0))
    pred = int(state.get("eligibility_prediction", 0))
    confidence = float(state.get("confidence", 0.0))
    report = state.get("validation_report") or []
    force_review = bool(state.get("force_review", False))

    has_high_issue = any(issue.get("severity") == "high" for issue in report)

    status = "REVIEW"
    reasons: List[Dict[str, Any]] = []
    if force_review or has_high_issue:
        status = "REVIEW"
        reasons.append(_reason("High-severity validation issues detected"))
    else:
        if score >= TAU_APPROVE and confidence >= C_MIN and pred == 1:
            status = "APPROVE"
            reasons.append(_reason(f"High eligibility score ({score:.2f}) with sufficient validation confidence ({confidence:.2f})"))
        elif score <= TAU_DECLINE or pred == 0:
            status = "SOFT_DECLINE"
            reasons.append(_reason(f"Low eligibility score ({score:.2f}) or model predicted ineligible"))
        else:
            status = "REVIEW"
            reasons.append(_reason(f"Borderline score ({score:.2f}) or insufficient confidence ({confidence:.2f})"))

    decision = {
        "status": status,
        "reasons": reasons,
        "score": score,
        "confidence": confidence
    }

    # --- LLM-synthesized enablement (with fallback) ---
    enablement_obj = _synthesize_enablement(validated, decision)
    enablement = enablement_obj.get("enablement_recommendations", [])
    enablement_summary = enablement_obj.get("overall_summary", "")

    return {
        "decision": decision,
        "enablement": enablement,
        "enablement_summary": enablement_summary
    }

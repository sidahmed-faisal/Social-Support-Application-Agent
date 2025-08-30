# orchestration/nodes/summarize_for_ui.py
from typing import Dict, Any, List

# Use your existing Ollama client (qwen2.5vl:3b)
try:
    from utils.ollama_utils import OllamaClient
except Exception:  # pragma: no cover
    from ollama_utils import OllamaClient  # fallback


def _format_recommendations_detail(enablement_recommendations: List[Dict[str, Any]]) -> str:
    """
    Produce a concise, structured text block that includes type, priority, rationale,
    and up to three suggested actions per recommendation.
    """
    if not enablement_recommendations:
        return "None"

    lines: List[str] = []
    for rec in enablement_recommendations[:5]:  # cap detail to top 5 for brevity
        rec_type = (rec.get("type") or "other")
        priority = (rec.get("priority") or "medium")
        rationale = (rec.get("rationale") or "").strip()
        actions = rec.get("suggested_actions") or []
        actions_str = "; ".join(map(str, actions[:3])) if actions else "N/A"

        lines.append(
            f"- type: {rec_type}\n"
            f"  priority: {priority}\n"
            f"  rationale: {rationale}\n"
            f"  suggested_actions: {actions_str}"
        )
    return "\n".join(lines)


def _build_summary_prompt(
    applicant_profile: Dict[str, Any],
    decision: Dict[str, Any],
    eligibility_score: float,
    enablement_summary: str,  # overall_summary string (if available)
    enablement_recommendations: List[Dict[str, Any]],
) -> str:
    """
    Create a concise prompt that instructs the model to return ONLY a JSON object:
      { "final_summary": "..." }
    NOTE: Similar applicants are intentionally **not** included.
    """
    # Extract readable decision reasons
    reasons_list = decision.get("reasons") or []
    reasons_text = "; ".join(
        (r.get("text", "") if isinstance(r, dict) else str(r)).strip()
        for r in reasons_list
        if r
    )

    # Build a structured recommendation detail section
    recommendations_detail = _format_recommendations_detail(enablement_recommendations)

    profile_section = (
        f"Name: {applicant_profile.get('name','Unknown')}\n"
        f"Emirates ID: {applicant_profile.get('emirates_id','Unknown')}\n"
        f"Monthly Income (AED): {applicant_profile.get('monthly_income', 0)}\n"
        f"Family Size: {applicant_profile.get('family_size', 1)}\n"
        f"Employment Status: {applicant_profile.get('employment_status','Unknown')}\n"
        f"Housing Type: {applicant_profile.get('housing_type','Unknown')}\n"
        f"Marital Status: {applicant_profile.get('marital_status','Unknown')}\n"
        f"Has Disability: {applicant_profile.get('has_disability', False)}\n"
        f"Nationality: {applicant_profile.get('nationality','Unknown')}\n"
        f"Credit Score: {applicant_profile.get('credit_score', 650)}\n"
        f"Net Worth (AED): {applicant_profile.get('net_worth', 0)}\n"
    )

    decision_section = (
        f"Decision: {decision.get('status','REVIEW')}\n"
        f"Eligibility Score: {eligibility_score:.2f}\n"
        f"Decision Reasons: {reasons_text or 'N/A'}\n"
        f"Validation Confidence: {decision.get('confidence', 0):.2f}\n"
    )

    enablement_section = (
        f"Enablement Overall Summary: {enablement_summary or 'N/A'}\n"
        "Enablement Recommendations Detail:\n"
        f"{recommendations_detail}\n"
    )

    return (
        "You are a public-sector caseworker assistant. Write a concise, human-readable FINAL SUMMARY "
        "for a benefits determination report. Keep it 4–7 lines. Include:\n"
        "1) Applicant identity basics (name, EID)\n"
        "2) Key financial/demographic signals (income, family, employment, housing)\n"
        "3) Eligibility score (two decimals) and the decision with short reasons\n"
        "4) A brief enablement summary AND a synthesis that reflects types, priorities, and rationales from the recommendations; "
        "optionally mention 1–3 specific suggested actions if helpful.\n"
        "Do NOT mention similar applicants.\n\n"
        "Return ONLY a JSON object with this schema:\n"
        "{\n"
        '  "final_summary": "string"\n'
        "}\n\n"
        "=== Applicant Profile ===\n"
        f"{profile_section}\n"
        "=== Decision Context ===\n"
        f"{decision_section}\n"
        "=== Enablement Context ===\n"
        f"{enablement_section}\n"
        "Think step-by-step but output only the JSON."
    )


def _manual_fallback_summary(
    applicant_profile: Dict[str, Any],
    decision: Dict[str, Any],
    eligibility_score: float,
    enablement_summary: str,
    enablement_recommendations: List[Dict[str, Any]],
) -> str:
    """Fallback if the LLM cannot produce valid JSON. No mention of similar applicants."""
    lines: List[str] = []
    lines.append(
        f"Applicant: {applicant_profile.get('name','Unknown')} | "
        f"EID: {applicant_profile.get('emirates_id','Unknown')}"
    )
    lines.append(
        "Signals: "
        f"Income {applicant_profile.get('monthly_income', 0)} AED, "
        f"Family {applicant_profile.get('family_size', 1)}, "
        f"Employment {applicant_profile.get('employment_status','Unknown')}, "
        f"Housing {applicant_profile.get('housing_type','Unknown')}"
    )
    lines.append(f"Eligibility score: {eligibility_score:.2f} | Decision: {decision.get('status','REVIEW')}")
    reasons = decision.get("reasons") or []
    if reasons:
        reasons_text = "; ".join(
            (r.get("text", "") if isinstance(r, dict) else str(r)).strip()
            for r in reasons
            if r
        )
        if reasons_text:
            lines.append(f"Reasons: {reasons_text}")

    # Include enablement details from recommendations
    if enablement_summary:
        lines.append(f"Enablement: {enablement_summary}")
    if enablement_recommendations:
        best = enablement_recommendations[0]
        rec_type = best.get("type", "other")
        priority = best.get("priority", "medium")
        rationale = (best.get("rationale") or "").strip()
        actions = best.get("suggested_actions") or []
        actions_str = "; ".join(map(str, actions[:3])) if actions else ""
        lines.append(f"Top enablement: {rec_type} ({priority}) — {rationale}")
        if actions_str:
            lines.append(f"Suggested actions: {actions_str}")

    return "\n".join(lines)


def summarize_for_ui(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce the final_summary using Ollama (JSON-coerced) with a rule-based fallback.
    Similar applicants are intentionally ignored.
    """
    applicant_profile: Dict[str, Any] = state.get("validated") or {}
    decision: Dict[str, Any] = state.get("decision") or {}
    eligibility_score: float = float(state.get("eligibility_score", 0.0))
    enablement_recommendations: List[Dict[str, Any]] = state.get("enablement") or []
    enablement_summary: str = state.get("enablement_summary") or ""

    ollama = OllamaClient()
    prompt = _build_summary_prompt(
        applicant_profile=applicant_profile,
        decision=decision,
        eligibility_score=eligibility_score,
        enablement_summary=enablement_summary,
        enablement_recommendations=enablement_recommendations,
    )
    schema = {"final_summary": "string"}

    result = ollama.structured_extraction(prompt, schema) or {}
    final_summary = ""
    if isinstance(result, dict):
        final_summary = str(result.get("final_summary") or "").strip()

    if not final_summary:
        final_summary = _manual_fallback_summary(
            applicant_profile=applicant_profile,
            decision=decision,
            eligibility_score=eligibility_score,
            enablement_summary=enablement_summary,
            enablement_recommendations=enablement_recommendations,
        )

    return {"final_summary": final_summary}

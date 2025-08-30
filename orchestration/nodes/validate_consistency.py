from typing import Dict, Any, List

def _range_check(value, lo, hi) -> bool:
    try:
        v = float(value)
        return (v >= lo) and (v <= hi)
    except Exception:
        return False

def validate_consistency(state: Dict[str, Any]) -> Dict[str, Any]:
    errors = state.get("errors", [])
    extracted = state.get("extracted") or {}
    report: List[Dict[str, Any]] = []
    confidence = 1.0
    force_review = False

    # --- Required fields must be present; treat as HIGH severity if missing ---
    required_fields = [
        "monthly_income", "family_size", "employment_status", "housing_type",
        "marital_status", "has_disability", "nationality", "credit_score", "net_worth"
    ]
    for f in required_fields:
        if f not in extracted:
            report.append({"field": f, "issue": "missing", "severity": "high"})
            confidence -= 0.20
            force_review = True

    # --- Plausibility checks (HIGH severity on hard out-of-range) ---
    if not _range_check(extracted.get("monthly_income", 0), 0, 100000):
        report.append({"field": "monthly_income", "issue": "out_of_range", "severity": "high"})
        confidence -= 0.25
        force_review = True

    if not _range_check(extracted.get("credit_score", 650), 300, 900):
        report.append({"field": "credit_score", "issue": "out_of_range", "severity": "high"})
        confidence -= 0.25
        force_review = True

    # Unknown categorical handling (informational/low)
    for cat in ["employment_status", "housing_type", "marital_status", "nationality"]:
        val = (extracted.get(cat) or "Unknown")
        if isinstance(val, str) and val.strip().lower() == "unknown":
            report.append({"field": cat, "issue": "unknown_value", "severity": "low"})
            confidence -= 0.05

    # Net worth can be negative; sanity cap (medium)
    if not _range_check(extracted.get("net_worth", 0), -1_000_000, 2_000_000):
        report.append({"field": "net_worth", "issue": "out_of_range", "severity": "medium"})
        confidence -= 0.10

    # --- Identity: missing/unknown EID or Name are HIGH severity and force review ---
    eid_val = extracted.get("emirates_id")
    if (eid_val in (None, "", "Unknown", "unknown")):
        report.append({"field": "emirates_id", "issue": "missing_or_unknown", "severity": "high"})
        confidence -= 0.20
        force_review = True

    name_val = extracted.get("name")
    if (name_val in (None, "", "Unknown", "unknown")):
        report.append({"field": "name", "issue": "missing_or_unknown", "severity": "high"})
        confidence -= 0.20
        force_review = True

    # Clamp confidence to [0,1]
    confidence = max(0.0, min(1.0, confidence))

    return {
        "validated": extracted,  # no mutation here
        "validation_report": report,
        "confidence": confidence,
        "force_review": force_review
    }

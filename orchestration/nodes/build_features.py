from typing import Dict, Any
import pandas as pd

CLASSIFIER_COLUMNS = [
    "monthly_income","family_size","employment_status","housing_type",
    "marital_status","has_disability","nationality","credit_score","net_worth"
]

def build_features(state: Dict[str, Any]) -> Dict[str, Any]:
    validated = state.get("validated") or {}
    # Build one-row DataFrame with the exact columns the classifier expects
    row = {col: validated.get(col) for col in CLASSIFIER_COLUMNS}
    # Fill sensible defaults if missing (mirroring consolidate defaults)
    row.setdefault("monthly_income", 0)
    row.setdefault("family_size", 1)
    row.setdefault("employment_status", "Unknown")
    row.setdefault("housing_type", "Unknown")
    row.setdefault("marital_status", "Unknown")
    row.setdefault("has_disability", False)
    row.setdefault("nationality", "Unknown")
    row.setdefault("credit_score", 650)
    row.setdefault("net_worth", 0)

    df = pd.DataFrame([row], columns=CLASSIFIER_COLUMNS)
    # We serialize DataFrame to JSON in state to avoid passing live objects
    features_df_json = {
        "columns": df.columns.tolist(),
        "data": df.to_dict(orient="records")
    }
    return {"features_df_json": features_df_json}

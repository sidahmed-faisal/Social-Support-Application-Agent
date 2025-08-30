from typing import Dict, Any
import pandas as pd

# Try both relative and absolute imports for flexibility
try:
    from model_training.eligibility_classifier import EligibilityClassifier
except Exception:  # pragma: no cover
    from eligibility_classifier import EligibilityClassifier  # fallback

def score_eligibility(state: Dict[str, Any]) -> Dict[str, Any]:
    features = state.get("features_df_json") or {}
    cols = features.get("columns") or []
    data = features.get("data") or []
    if not cols or not data:
        return {"eligibility_score": 0.0, "eligibility_prediction": 0}

    df = pd.DataFrame(data, columns=cols)
    # Load the already-trained model
    clf = EligibilityClassifier.load("eligibility_model.pkl")
    score = float(clf.predict_proba(df)[0][1])
    pred = int(clf.predict(df)[0])
    return {"eligibility_score": score, "eligibility_prediction": pred}

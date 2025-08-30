from typing import TypedDict, List, Dict, Any, Optional

# Single shared state across LangGraph nodes
class AppState(TypedDict, total=False):
    # Inputs
    file_paths: List[str]

    # Extraction
    extracted: Dict[str, Any]
    raw_extraction_logs: List[str]

    # Validation
    validated: Dict[str, Any]
    validation_report: List[Dict[str, Any]]
    confidence: float
    force_review: bool

    # Features / Model
    features_df_json: Dict[str, Any]  # to avoid passing live DataFrame through state
    eligibility_score: float
    eligibility_prediction: int

    # Decision
    decision: Dict[str, Any]
    enablement: List[Dict[str, Any]]

    # Storage / Retrieval
    embedding: List[float]
    point_id: Optional[str]
    similar_applicants: List[Dict[str, Any]]

    # Output
    final_summary: str

    # Errors
    errors: List[str]

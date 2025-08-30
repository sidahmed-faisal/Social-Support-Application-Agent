# orchestration/graph.py
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END

from .state import AppState
from .nodes.ingest_extract import ingest_extract
from .nodes.validate_consistency import validate_consistency
from .nodes.build_features import build_features
from .nodes.score_eligibility import score_eligibility
from .nodes.decide_and_recommend import decide_and_recommend
from .nodes.vector_store_and_similar import vector_store_and_similar
from .nodes.summarize_for_ui import summarize_for_ui

def build_graph():
    workflow = StateGraph(AppState)

    # Nodes
    workflow.add_node("ingest_extract", ingest_extract)
    workflow.add_node("validate_consistency", validate_consistency)
    workflow.add_node("build_features", build_features)
    workflow.add_node("score_eligibility", score_eligibility)
    workflow.add_node("decide_and_recommend", decide_and_recommend)
    workflow.add_node("summarize_for_ui", summarize_for_ui)
    workflow.add_node("vector_store_and_similar", vector_store_and_similar)

    # Edges (summary BEFORE vector store so we can store applicant_summary)
    workflow.add_edge(START, "ingest_extract")
    workflow.add_edge("ingest_extract", "validate_consistency")
    workflow.add_edge("validate_consistency", "build_features")
    workflow.add_edge("build_features", "score_eligibility")
    workflow.add_edge("score_eligibility", "decide_and_recommend")
    workflow.add_edge("decide_and_recommend", "summarize_for_ui")
    workflow.add_edge("summarize_for_ui", "vector_store_and_similar")
    workflow.add_edge("vector_store_and_similar", END)

    return workflow.compile()

def run(file_paths):
    graph = build_graph()
    init_state: Dict[str, Any] = {"file_paths": file_paths}
    return graph.invoke(init_state)

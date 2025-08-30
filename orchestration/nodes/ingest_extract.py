from typing import Dict, Any
from file_processor.file_processor import FileProcessor

def ingest_extract(state: Dict[str, Any]) -> Dict[str, Any]:
    errors = state.get("errors", [])
    try:
        file_paths = state.get("file_paths") or []
        if not file_paths:
            return {"errors": errors + ["ingest_extract: no file_paths provided"]}

        fp = FileProcessor()
        extracted = fp.process_files(file_paths)
        return {
            "extracted": extracted
        }
    except Exception as e:
        errors.append(f"ingest_extract error: {e}")
        return {"errors": errors}

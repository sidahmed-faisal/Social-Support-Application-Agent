from utils.ollama_utils import OllamaClient
from typing import Dict, Any

class EmiratesIDProcessor:
    def __init__(self):
        self.ollama = OllamaClient()
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """Extract data from Emirates ID image"""
        try:
            prompt = """Extract the following information from this Emirates ID card. 
                        Return ONLY a valid JSON object with these exact keys:
                        - name (string)
                        - emirates_id (string, format: 784-YYYY-XXXXXXX-D)
                        - date_of_birth (string, YYYY-MM-DD format if possible)
                        - nationality (string)
                        - gender (string: Male/Female)
                        - employment_status (string: Employed/Unemployed/Self-employed)
                        - marital_status (string: Single/Married/Divorced)
                        - has_disability (boolean)
                        - address (string)
                        """
            
            extracted_data = self.ollama.extract_text_from_image(file_path, prompt)
            print(f"Raw LLM response: {extracted_data}")
            
            # Extract JSON from the response
            parsed_data = self.ollama.extract_json_from_response(extracted_data)
            print(f"Parsed data: {parsed_data}")
            
            if parsed_data:
                return parsed_data
            else:
                # Fallback to manual extraction if LLM fails
                return self._fallback_extraction(file_path)
        except Exception as e:
            print(f"Error processing Emirates ID: {str(e)}")
            return {"error": f"Failed to process Emirates ID: {str(e)}"}
    
    def _fallback_extraction(self, file_path: str) -> Dict[str, Any]:
        """Fallback extraction method"""
        return {
            "name": "Unknown",
            "emirates_id": "784-0000-0000000-0",
            "date_of_birth": "1970-01-01",
            "nationality": "Unknown",
            "gender": "Unknown",
            "employment_status": "Unknown",
            "marital_status": "Unknown",
            "has_disability": False,
            "address": "Unknown"
        }
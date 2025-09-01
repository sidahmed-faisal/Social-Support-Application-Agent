from utils.ollama_utils import OllamaClient
from typing import Dict, Any

class CreditReportProcessor:
    def __init__(self):
        self.ollama = OllamaClient()
    
    def process(self, file_path: str) -> Dict[str, Any]:
        """Extract data from credit report PDF"""
        try:
            prompt = """Extract the following information from this credit report.
            Return ONLY a valid JSON object with these exact keys:
            - emirates_id (string)
            - applicant_name (string)
            - credit_score (integer)
            - total_credit_limit (float, in AED)
            - total_outstanding (float, in AED)
            - monthly_income_reported (float, in AED)
            - housing_type (string: Owned, Rented, Shared, or Unknown)

            if for any field the information is not available or the field not available, return "Unknown" or 0 for numeric fields.
            }"""
            
            extracted_data = self.ollama.extract_text_from_pdf(file_path, prompt)
            print(f"Raw LLM response: {extracted_data}")
            
            # Extract JSON from the response
            parsed_data = self.ollama.extract_json_from_response(extracted_data)
            print(f"Parsed data: {parsed_data}")
            
            if parsed_data:
                return {
                    "credit_score": int(parsed_data.get("credit_score", 0)),
                    "total_credit_limit": float(parsed_data.get("total_credit_limit", 0)),
                    "total_outstanding": float(parsed_data.get("total_outstanding", 0)),
                    "monthly_income_reported": float(parsed_data.get("monthly_income_reported", 0)),
                    "housing_type": parsed_data.get("housing_type", "Unknown")
                }
            else:
                # Fallback to default values if parsing fails
                return {
                    "credit_score": 650,
                    "total_credit_limit": 0,
                    "total_outstanding": 0,
                    "monthly_income_reported": 0,
                    "housing_type": "Unknown"
                }
        except Exception as e:
            print(f"Error processing credit report: {str(e)}")
            return {"error": f"Failed to process credit report: {str(e)}"}
import requests
import json
import base64
import re
from typing import Dict, Any, List

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
    
    def extract_text_from_image(self, image_path: str, prompt: str) -> str:
        """Extract text from image using Qwen2.5vl"""
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
        payload = {
            "model": "qwen2.5vl:3b",
            "prompt": prompt,
            "images": [image_data],
            "stream": False
        }
        
        response = requests.post(f"{self.base_url}/api/generate", json=payload)
        return response.json().get("response", "")
    
    def extract_text_from_pdf(self, pdf_path: str, prompt: str) -> str:
        """Extract text from PDF using qwen2.5vl:3b"""
        # For PDFs, we'll read the text and send to LLM
        import PyPDF2
        
        text = ""
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        payload = {
            "model": "qwen2.5vl:3b",
            "prompt": f"{prompt}\n\nDocument text:\n{text[:4000]}",  # Limit context
            "stream": False
        }
        
        response = requests.post(f"{self.base_url}/api/generate", json=payload)
        return response.json().get("response", "")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        payload = {
            "model": "all-minilm:latest",
            "prompt": text
        }
        
        response = requests.post(f"{self.base_url}/api/embeddings", json=payload)
        return response.json().get("embedding", [])
    
    def structured_extraction(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from text using LLM"""
        schema_str = json.dumps(schema, indent=2)
        prompt = f"""Extract the following information from the text below. 
        Return ONLY a valid JSON object matching this schema: {schema_str}
        
        Text: {text}
        
        JSON:"""
        
        payload = {
            "model": "qwen2.5vl:3b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        response = requests.post(f"{self.base_url}/api/generate", json=payload)
        try:
            return json.loads(response.json().get("response", "{}"))
        except:
            return {}
    
    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response that might contain additional text
        """
        try:
            # Try to parse the entire response as JSON first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the response
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, response_text)
            
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    # Try to clean up common JSON issues
                    cleaned_json = self._clean_json_string(match.group())
                    try:
                        return json.loads(cleaned_json)
                    except json.JSONDecodeError:
                        pass
            
            # If all else fails, return empty dict
            return {}
    
    def _clean_json_string(self, json_string: str) -> str:
        """Clean common JSON formatting issues"""
        # Remove trailing commas
        json_string = re.sub(r',\s*}', '}', json_string)
        json_string = re.sub(r',\s*]', ']', json_string)
        
        # Fix single quotes to double quotes
        json_string = re.sub(r"'([^']*)'", r'"\1"', json_string)
        
        # Remove any non-printable characters
        json_string = ''.join(char for char in json_string if char.isprintable() or char in ' \t\n\r')
        
        return json_string
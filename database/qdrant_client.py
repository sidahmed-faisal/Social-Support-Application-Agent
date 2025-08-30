from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
from typing import List, Dict, Any
import uuid

class QdrantStorage:
    def __init__(self, host="localhost", port=6333, collection_name="applicants"):
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = collection_name
        self._create_collection()
    
    def _create_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Using all-MiniLM-L6-v2 embedding size
                    distance=models.Distance.COSINE
                )
            )
    
    def _create_text_content(self, applicant_data: Dict[str, Any]) -> str:
        """Create comprehensive text content for embedding and retrieval"""
        text_content = f"""
        Applicant: {applicant_data.get('name', 'Unknown')}
        Emirates ID: {applicant_data.get('emirates_id', 'Unknown')}
        Monthly Income: {applicant_data.get('monthly_income', 0)}
        Family Size: {applicant_data.get('family_size', 1)}
        Employment Status: {applicant_data.get('employment_status', 'Unknown')}
        Housing Type: {applicant_data.get('housing_type', 'Unknown')}
        Marital Status: {applicant_data.get('marital_status', 'Unknown')}
        Has Disability: {applicant_data.get('has_disability', False)}
        Nationality: {applicant_data.get('nationality', 'Unknown')}
        Credit Score: {applicant_data.get('credit_score', 650)}
        Net Worth: {applicant_data.get('net_worth', 0)}
        Eligibility Score: {applicant_data.get('eligibility_score', 0)}
        Eligibility Prediction: {applicant_data.get('eligibility_prediction', 0)}
        """
        
        # Add decision information
        if 'decision' in applicant_data:
            decision = applicant_data['decision']
            text_content += f"""
        Decision Status: {decision.get('status', 'Unknown')}
        Decision Score: {decision.get('score', 'Unknown')}
        Decision Confidence: {decision.get('confidence', 'Unknown')}
        """
            if 'reasons' in decision:
                reasons = [reason.get('text', '') for reason in decision.get('reasons', [])]
                text_content += f"        Decision Reasons: {', '.join(reasons)}\n"
        
        # Add enablement and recommendations
        if 'enablment_and_recommendations' in applicant_data:
            enablement = applicant_data['enablment_and_recommendations']
            text_content += f"""
        Applicant Summary: {enablement.get('applicant_summary', '')}
        """
            if 'recommendations' in enablement:
                for i, rec in enumerate(enablement.get('recommendations', [])):
                    text_content += f"""
        Recommendation {i+1}:
          Type: {rec.get('type', '')}
          Rationale: {rec.get('rationale', '')}
          Suggested Actions: {', '.join(rec.get('suggested_actions', []))}
        """
        
        return text_content.strip()
    
    def store_applicant(self, applicant_data: Dict[str, Any], embedding: List[float]):
        """Store applicant data with embedding and text field for LangChain"""
        # Use applicant_id as UUID (emirates_id)
        point_id = str(uuid.uuid4())
        
        # Create text content for embedding and retrieval
        text_content = self._create_text_content(applicant_data)
        
        # Prepare payload with both structured data and text field
        payload = {
            **applicant_data,  # Include all applicant data
            "text": text_content  # Add text field for LangChain
        }
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,  # Use applicant_id as point ID
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return point_id
    
    def search_similar_applicants(self, embedding: List[float], limit: int = 5):
        """Search for similar applicants"""
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=limit,
            with_payload=True  # Ensure payload is returned
        )
from file_processor.bank_statement_processor import BankStatementProcessor
from file_processor.assets_liabilities_processor import AssetsLiabilitiesProcessor
from file_processor.credit_report_processor import CreditReportProcessor
from file_processor.emirates_id_processor import EmiratesIDProcessor
from typing import Dict, Any, List
import os

class FileProcessor:
    def __init__(self):
        self.processors = {
            '.csv': BankStatementProcessor(),
            '.xlsx': AssetsLiabilitiesProcessor(),
            '.pdf': CreditReportProcessor(),
            '.png': EmiratesIDProcessor(),
            '.jpg': EmiratesIDProcessor(),
            '.jpeg': EmiratesIDProcessor()
        }
    
    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process all files and extract relevant data"""
        result = {}
        
        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in self.processors:
                processor = self.processors[ext]
                file_data = processor.process(file_path)
                
                # Categorize the data based on file type
                if ext == '.csv':
                    result['bank_statement'] = file_data
                elif ext == '.xlsx':
                    result['assets_liabilities'] = file_data
                elif ext == '.pdf':
                    result['credit_report'] = file_data
                elif ext in ['.png', '.jpg', '.jpeg']:
                    result['emirates_id'] = file_data
        
        return self._consolidate_data(result)
    
# In file_processor/file_processor.py, update the _consolidate_data method:

    def _consolidate_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate data from all sources into a unified format"""
        consolidated = {
            "monthly_income": 0,
            "family_size": 1,
            "employment_status": "Unknown",
            "housing_type": "Unknown",
            "marital_status": "Unknown",
            "has_disability": False,
            "nationality": "Unknown",
            "credit_score": 650,
            "net_worth": 0,
            "name": "Unknown",
            "emirates_id": "Unknown"
        }
        
        # Extract from bank statement
        if 'bank_statement' in extracted_data and not extracted_data['bank_statement'].get('error'):
            bank_data = extracted_data['bank_statement']
            if 'estimated_monthly_income' in bank_data:
                consolidated['monthly_income'] = bank_data['estimated_monthly_income']
            if 'account_holder' in bank_data and bank_data['account_holder'] not in ["Unknown", "unknown"]:
                consolidated['name'] = bank_data['account_holder']
            if 'emirates_id' in bank_data and bank_data['emirates_id'] not in ["Unknown", "unknown"]:
                consolidated['emirates_id'] = bank_data['emirates_id']
        
        # Extract from assets/liabilities
        if 'assets_liabilities' in extracted_data and not extracted_data['assets_liabilities'].get('error'):
            assets_data = extracted_data['assets_liabilities']
            if 'net_worth' in assets_data:
                consolidated['net_worth'] = assets_data['net_worth']
        
        # Extract from credit report
        if 'credit_report' in extracted_data and not extracted_data['credit_report'].get('error'):
            credit_data = extracted_data['credit_report']
            if 'credit_score' in credit_data:
                consolidated['credit_score'] = credit_data['credit_score']
            if 'monthly_income_reported' in credit_data and credit_data['monthly_income_reported'] > 0:
                consolidated['monthly_income'] = credit_data['monthly_income_reported']
            if 'housing_type' in credit_data:
                consolidated['housing_type'] = credit_data['housing_type']
            if 'emirates_id' in credit_data and credit_data['emirates_id'] not in ["Unknown", "unknown"]:
                consolidated['emirates_id'] = credit_data['emirates_id']
        
        # Extract from Emirates ID
        if 'emirates_id' in extracted_data and not extracted_data['emirates_id'].get('error'):
            id_data = extracted_data['emirates_id']
            if 'name' in id_data and id_data['name'] not in ["Unknown", "unknown"]:
                consolidated['name'] = id_data['name']
            if 'emirates_id' in id_data and id_data['emirates_id'] not in ["Unknown", "unknown"]:
                consolidated['emirates_id'] = id_data['emirates_id']
            if 'nationality' in id_data and id_data['nationality'] not in ["Unknown", "unknown"]:
                consolidated['nationality'] = id_data['nationality']

            if 'employment_status' in id_data and id_data['employment_status'] not in ["Unknown", "unknown"]:
                consolidated['employment_status'] = id_data['employment_status']
            if 'marital_status' in id_data and id_data['marital_status'] not in ["Unknown", "unknown"]:
                consolidated['marital_status'] = id_data['marital_status']
            if 'has_disability' in id_data:
                consolidated['has_disability'] = bool(id_data['has_disability'])
        
        return consolidated
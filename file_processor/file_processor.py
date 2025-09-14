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
        """
        Consolidate data from all sources into a unified format.
        Emirates ID data takes priority for identity fields (name, emirates_id, nationality).
        """
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
        
        # Track inconsistencies for logging
        inconsistencies = []
        
        # STEP 1: Extract Emirates ID data first (highest priority for identity)
        emirates_name = None
        emirates_id = None
        emirates_nationality = None
        
        if 'emirates_id' in extracted_data and not extracted_data['emirates_id'].get('error'):
            id_data = extracted_data['emirates_id']
            
            # Extract identity fields from Emirates ID
            if 'name' in id_data and id_data['name'] not in ["Unknown", "unknown", ""]:
                emirates_name = id_data['name'].strip()
                consolidated['name'] = emirates_name
                
            if 'emirates_id' in id_data and id_data['emirates_id'] not in ["Unknown", "unknown", ""]:
                emirates_id = id_data['emirates_id'].strip()
                consolidated['emirates_id'] = emirates_id
                
            if 'nationality' in id_data and id_data['nationality'] not in ["Unknown", "unknown", ""]:
                emirates_nationality = id_data['nationality'].strip()
                consolidated['nationality'] = emirates_nationality
                
            # Other Emirates ID fields
            if 'employment_status' in id_data and id_data['employment_status'] not in ["Unknown", "unknown", ""]:
                consolidated['employment_status'] = id_data['employment_status']
            if 'marital_status' in id_data and id_data['marital_status'] not in ["Unknown", "unknown", ""]:
                consolidated['marital_status'] = id_data['marital_status']
            if 'has_disability' in id_data:
                consolidated['has_disability'] = bool(id_data['has_disability'])
        
        # STEP 2: Extract from other sources, checking for inconsistencies
        
        # Bank statement data
        if 'bank_statement' in extracted_data and not extracted_data['bank_statement'].get('error'):
            bank_data = extracted_data['bank_statement']
            
            # Financial data
            if 'estimated_monthly_income' in bank_data:
                consolidated['monthly_income'] = bank_data['estimated_monthly_income']
            
            # Check for identity inconsistencies
            if 'account_holder' in bank_data and bank_data['account_holder'] not in ["Unknown", "unknown", ""]:
                bank_name = bank_data['account_holder'].strip()
                if emirates_name and bank_name.lower() != emirates_name.lower():
                    inconsistencies.append({
                        "field": "name",
                        "emirates_id_value": emirates_name,
                        "bank_statement_value": bank_name,
                        "source": "bank_statement"
                    })
                # Only use bank name if Emirates ID name is not available
                if not emirates_name:
                    consolidated['name'] = bank_name
            
            if 'emirates_id' in bank_data and bank_data['emirates_id'] not in ["Unknown", "unknown", ""]:
                bank_eid = bank_data['emirates_id'].strip()
                if emirates_id and bank_eid != emirates_id:
                    inconsistencies.append({
                        "field": "emirates_id", 
                        "emirates_id_value": emirates_id,
                        "bank_statement_value": bank_eid,
                        "source": "bank_statement"
                    })
                # Only use bank EID if Emirates ID is not available
                if not emirates_id:
                    consolidated['emirates_id'] = bank_eid
        
        # Credit report data
        if 'credit_report' in extracted_data and not extracted_data['credit_report'].get('error'):
            credit_data = extracted_data['credit_report']
            
            # Financial/scoring data
            if 'credit_score' in credit_data:
                consolidated['credit_score'] = credit_data['credit_score']
            if 'monthly_income_reported' in credit_data and credit_data['monthly_income_reported'] > 0:
                # Use higher of bank statement or credit report income
                consolidated['monthly_income'] = max(
                    consolidated['monthly_income'], 
                    credit_data['monthly_income_reported']
                )
            if 'housing_type' in credit_data:
                consolidated['housing_type'] = credit_data['housing_type']
            
            # Check for identity inconsistencies
            if 'emirates_id' in credit_data and credit_data['emirates_id'] not in ["Unknown", "unknown", ""]:
                credit_eid = credit_data['emirates_id'].strip()
                if emirates_id and credit_eid != emirates_id:
                    inconsistencies.append({
                        "field": "emirates_id",
                        "emirates_id_value": emirates_id,
                        "credit_report_value": credit_eid,
                        "source": "credit_report"
                    })
                # Only use credit report EID if Emirates ID is not available
                if not emirates_id:
                    consolidated['emirates_id'] = credit_eid
        
        # Assets/liabilities data
        if 'assets_liabilities' in extracted_data and not extracted_data['assets_liabilities'].get('error'):
            assets_data = extracted_data['assets_liabilities']
            if 'net_worth' in assets_data:
                consolidated['net_worth'] = assets_data['net_worth']
        
        # STEP 3: Log inconsistencies if any found
        if inconsistencies:
            consolidated['_inconsistencies'] = inconsistencies
            print(f"⚠️  Identity inconsistencies detected: {len(inconsistencies)} issues")
            # Fixed version - no nested f-string brackets
            for inc in inconsistencies:
                source = inc['source']
                source_value_key = f"{source}_value"
                source_value = inc.get(source_value_key, 'N/A')
                print(f"   - {inc['field']}: Emirates ID='{inc['emirates_id_value']}' vs {source}='{source_value}'")
        return consolidated
import pandas as pd
from typing import Dict, Any

class BankStatementProcessor:
    @staticmethod
    def process(file_path: str) -> Dict[str, Any]:
        """Extract data from bank statement CSV"""
        try:
            df = pd.read_csv(file_path)
            
            # Extract relevant information
            result = {
                "emirates_id": df['emirates_id'].iloc[0] if 'emirates_id' in df.columns else "Unknown",
                "average_balance": float(df['balance'].mean()) if 'balance' in df.columns else 0,
                "total_credits": float(df[df['amount'] > 0]['amount'].sum()) if 'amount' in df.columns else 0,
                "total_debits": float(-df[df['amount'] < 0]['amount'].sum()) if 'amount' in df.columns else 0,
                "bank_name": df['bank_name'].iloc[0] if 'bank_name' in df.columns else "Unknown",
                "account_holder": df['applicant_name'].iloc[0] if 'applicant_name' in df.columns else "Unknown",
            }
            
            # Estimate monthly income from salary credits
            if 'description' in df.columns and 'amount' in df.columns:
                salary_credits = df[df['description'].str.contains('SALARY', case=False, na=False)]
                if not salary_credits.empty:
                    result["estimated_monthly_income"] = float(salary_credits['amount'].max())
            
            return result
        except Exception as e:
            return {"error": f"Failed to process bank statement: {str(e)}"}
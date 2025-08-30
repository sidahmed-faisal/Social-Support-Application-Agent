import pandas as pd
from typing import Dict, Any

class AssetsLiabilitiesProcessor:
    @staticmethod
    def process(file_path: str) -> Dict[str, Any]:
        """Extract data from assets/liabilities Excel"""
        try:
            assets_df = pd.read_excel(file_path, sheet_name='Assets')
            liabilities_df = pd.read_excel(file_path, sheet_name='Liabilities')
            
            total_assets = assets_df['Value (AED)'].sum() if not assets_df.empty else 0
            total_liabilities = liabilities_df['Amount (AED)'].sum() if not liabilities_df.empty else 0
            
            return {
                "total_assets": float(total_assets),
                "total_liabilities": float(total_liabilities),
                "net_worth": float(total_assets - total_liabilities)
            }
        except Exception as e:
            return {"error": f"Failed to process assets/liabilities: {str(e)}"}
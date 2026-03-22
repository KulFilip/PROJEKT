
# verify_fixes.py
import pandas as pd
from database import DatabaseManager
from analysis import Analyzer, comprehensive_leakage_test
import config

def run_verification():
    print("🚀 Running Leakage Verification Script...")
    db = DatabaseManager()
    symbol = 'XAUUSD'
    
    # 1. Load swings
    swings = db.load_swings(symbol)
    if swings.empty:
        print(f"❌ No swings found for {symbol}. Run analysis first.")
        return
    
    print(f"Loaded {len(swings)} swings for {symbol}")
    
    # 2. Run the test
    success = comprehensive_leakage_test(swings)
    
    if success:
        print("\n🏆 VERIFICATION SUCCESSFUL: No data leakage detected.")
    else:
        print("\n❌ VERIFICATION FAILED: Data leakage or other issues detected.")

if __name__ == "__main__":
    run_verification()

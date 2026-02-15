"""
Daily NIFTY Data Update Script

Run this script daily to add the latest day's trading data to nifty_close.csv
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.nifty_data_manager import NiftyDataManager
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description="Update NIFTY historical data")
    parser.add_argument('--date', type=str, help='Date (DD-MMM-YYYY or YYYY-MM-DD)', 
                       default=datetime.now().strftime('%d-%b-%Y'))
    parser.add_argument('--open', type=float, required=True, help='Opening price')
    parser.add_argument('--high', type=float, required=True, help='High price')
    parser.add_argument('--low', type=float, required=True, help='Low price')
    parser.add_argument('--close', type=float, required=True, help='Closing price')
    parser.add_argument('--volume', type=int, default=0, help='Volume (Shares Traded)')
    parser.add_argument('--turnover', type=float, default=0.0, help='Turnover in Cr')
    
    args = parser.parse_args()
    
    manager = NiftyDataManager()
    
    print("=" * 60)
    print("DAILY NIFTY DATA UPDATE")
    print("=" * 60)
    
    manager.add_daily_update(
        date_str=args.date,
        open_val=args.open,
        high=args.high,
        low=args.low,
        close=args.close,
        volume=args.volume,
        turnover=args.turnover
    )
    
    print("\n")
    manager.get_summary()


if __name__ == "__main__":
    main()

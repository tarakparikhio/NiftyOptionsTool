#!/usr/bin/env python
"""
Test Auto-Fetch NIFTY Data Feature

Demonstrates automatic data fetching from Yahoo Finance API
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_clients.market_data import MarketDataClient
from utils.nifty_data_manager import NiftyDataManager


def test_auto_fetch():
    """Test the auto-fetch workflow"""
    print("=" * 60)
    print("🔄 AUTO-FETCH NIFTY DATA TEST")
    print("=" * 60)
    print()
    
    # Step 1: Fetch from API
    print("📡 Step 1: Fetching from Yahoo Finance API...")
    client = MarketDataClient()
    data = client.fetch_nifty(use_cache=False)
    
    if not data:
        print("❌ API fetch failed")
        return False
    
    print("✅ Fetch successful!")
    print(f"   Date: {data['date']}")
    print(f"   Open: ₹{data['open']:,.2f}")
    print(f"   High: ₹{data['high']:,.2f}")
    print(f"   Low: ₹{data['low']:,.2f}")
    print(f"   Close: ₹{data['close']:,.2f}")
    print(f"   Volume: {data.get('volume', 0):,}")
    print()
    
    # Step 2: Validate OHLC
    print("✅ Step 2: Validating OHLC relationships...")
    if data['high'] < data['low']:
        print("❌ Validation failed: High < Low")
        return False
    if data['close'] > data['high'] or data['close'] < data['low']:
        print("❌ Validation failed: Close outside High-Low range")
        return False
    if data['open'] > data['high'] or data['open'] < data['low']:
        print("❌ Validation failed: Open outside High-Low range")
        return False
    print("   All OHLC checks passed!")
    print()
    
    # Step 3: Update CSV
    print("💾 Step 3: Updating nifty_close.csv...")
    manager = NiftyDataManager()
    
    try:
        manager.add_daily_update(
            date_str=data['date'],
            open_val=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            volume=data.get('volume', 0)
        )
        print("✅ CSV updated successfully!")
        print()
    except Exception as e:
        print(f"❌ Update failed: {e}")
        return False
    
    # Step 4: Verify update
    print("🔍 Step 4: Verifying update...")
    manager.get_summary()
    print()
    
    print("=" * 60)
    print("✅ AUTO-FETCH TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print()
    print("📊 Next steps:")
    print("   1. Open dashboard at http://localhost:8501")
    print("   2. Go to sidebar → Expand 'NIFTY Data Update'")
    print("   3. Click '🚀 Auto-Fetch from API'")
    print("   4. Refresh page to see updated candlestick chart")
    print()
    
    return True


if __name__ == "__main__":
    test_auto_fetch()

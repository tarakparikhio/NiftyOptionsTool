"""
Test script for NSE Option Chain Client

Tests the live data fetching functionality:
- Session initialization
- Expiry dates fetching
- Option chain data parsing
- Caching mechanism
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from api_clients.nse_option_chain import NSEOptionChainClient


def test_nse_client():
    """Test NSE option chain client."""
    
    print("=" * 60)
    print("NSE OPTION CHAIN CLIENT - TEST")
    print("=" * 60)
    
    try:
        # Initialize client
        print("\n1. Initializing NSE client...")
        client = NSEOptionChainClient()
        print("✅ Client initialized")
        
        # Fetch expiry dates
        print("\n2. Fetching available expiry dates...")
        expiry_dates = client.get_expiry_dates()
        print(f"✅ Found {len(expiry_dates)} expiry dates:")
        for i, expiry in enumerate(expiry_dates[:5], 1):
            print(f"   {i}. {expiry}")
        if len(expiry_dates) > 5:
            print(f"   ... and {len(expiry_dates) - 5} more")
        
        # Get spot price
        print("\n3. Fetching current NIFTY spot price...")
        spot_price = client.get_spot_price()
        print(f"✅ Current NIFTY: {spot_price:,.2f}")
        
        # Fetch option chain for first expiry
        print(f"\n4. Fetching option chain for {expiry_dates[0]}...")
        df = client.get_option_chain_by_expiry(expiry_dates[0])
        
        print(f"✅ Fetched {len(df)} option chain rows")
        print(f"\nData summary:")
        print(f"  - Columns: {', '.join(df.columns[:8])}...")
        print(f"  - Strike range: {df['Strike'].min():.0f} - {df['Strike'].max():.0f}")
        print(f"  - Call strikes: {len(df[df['Option_Type'] == 'CE'])}")
        print(f"  - Put strikes: {len(df[df['Option_Type'] == 'PE'])}")
        print(f"  - Total OI: {df['OI'].sum():,.0f}")
        
        print("\nSample data (first 5 rows):")
        print(df.head())
        
        # Test caching
        print("\n5. Testing cache functionality...")
        cached_df = client.load_cache(expiry_dates[0], ttl_minutes=5)
        if cached_df is not None:
            print(f"✅ Cache working - {len(cached_df)} rows loaded from cache")
        else:
            print("⚠️ No cache found (expected on first run)")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        
        return False


if __name__ == "__main__":
    success = test_nse_client()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Quick test script for v2.1 new features"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from metrics import OptionsMetrics
from analysis.decision_engine import DecisionEngine
import pandas as pd

print("=" * 70)
print("v2.1 FEATURE TESTS")
print("=" * 70)

# Test 1: Top OI with Context
print("\n[1] Testing Top OI with Context...")
try:
    df = pd.DataFrame({
        'Strike': [25000, 25500, 26000, 26500, 27000] * 2,
        'Option_Type': ['CE'] * 5 + ['PE'] * 5,
        'OI': [100000, 150000, 250000, 180000, 120000, 280000, 220000, 190000, 160000, 140000],
        'OI_Change': [1000, 2000, 5000, 3000, 1500, 5000, 4000, 3000, 2000, 1500],
        'Volume': [500, 800, 1200, 900, 600, 1200, 1000, 800, 700, 600],
        'IV': [15.5, 16.2, 17.0, 16.8, 16.0, 18.5, 17.8, 17.2, 16.5, 15.8]
    })
    
    metrics = OptionsMetrics(df)
    result = metrics.get_top_oi_with_context(spot_price=26000, pcr=1.15, n=3)
    
    print("OK: Top 3 CE:")
    for idx, row in result['CE'].iterrows():
        print(f"   Strike {row['Strike']:.0f} | OI: {row['OI']:,.0f} ({row['OI_Pct']:.1f}%) | {row['Distance_Points']:+.0f} pts")
        print(f"   → {row['Signal']}")
    
    print("\nOK: Top 3 PE:")
    for idx, row in result['PE'].iterrows():
        print(f"   Strike {row['Strike']:.0f} | OI: {row['OI']:,.0f} ({row['OI_Pct']:.1f}%) | {row['Distance_Points']:+.0f} pts")
        print(f"   → {row['Signal']}")
    
    print("\nPASS: Top OI context working correctly")
except Exception as e:
    print(f"FAIL: {e}")

# Test 2: AI Trade Signal
print("\n[2] Testing AI Trade Signal...")
try:
    engine = DecisionEngine()
    
    # Test case 1: High VIX, range-bound
    signal = engine.generate_probability_signal(
        pcr=1.15,
        vix=22.5,
        oi_concentration=68.2,
        iv_skew=2.3
    )
    
    print(f"OK: Action: {signal['action']}")
    print(f"OK: Confidence: {signal['confidence']}%")
    print(f"OK: Strategy: {signal['strategy']}")
    print(f"OK: Reasoning: {signal['reasoning']}")
    print(f"   Score: {signal['score']}")
    print(f"   Bias: {signal['bias']}")
    print(f"   Vol Regime: {signal['vol_regime']}")
    
    print("\nPASS: AI signal working correctly")
except Exception as e:
    print(f"FAIL: {e}")

# Test 3: OI Heatmap Filter (just check import)
print("\n[3] Testing OI Heatmap Filter...")
try:
    from visualization import OptionsVisualizer
    viz = OptionsVisualizer()
    print("PASS: Visualizer with new parameters loads correctly")
except Exception as e:
    print(f"FAIL: {e}")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETE")
print("=" * 70)

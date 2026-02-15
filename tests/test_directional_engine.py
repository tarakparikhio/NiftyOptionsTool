#!/usr/bin/env python3
"""
Integration Validation Script

⚠️ NOTE: This test uses the legacy strategy_builder API
   (archived in archive/legacy_v1.0/strategy_builder_old.py)
   
   For new strategy builder tests, see tests/test_strategy_logic.py

Verifies that all components are working and properly integrated.
Run this before using the trading engine in production.
"""

import sys
import pandas as pd
import numpy as np
from typing import Tuple

def test_imports() -> bool:
    """Test that all new components import correctly."""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)
    
    try:
        from analysis.directional_signal import DirectionalSignalEngine
        print("✅ DirectionalSignalEngine imported")
        
        # NOTE: Using archived legacy version for this test
        sys.path.append('archive/legacy_v1.0')
        from strategy_builder_old import StrategyTemplate
        sys.path.remove('archive/legacy_v1.0')
        print("✅ StrategyTemplate imported (legacy)")
        
        from analysis.position_sizer import PositionSizer
        print("✅ PositionSizer imported")
        
        from analysis.range_predictor import RangePredictor
        print("✅ RangePredictor imported")
        
        from analysis.decision_engine import DecisionEngine
        print("✅ DecisionEngine imported")
        
        from analysis.directional_workflow import DirectionalTradingWorkflow
        print("✅ DirectionalTradingWorkflow imported")
        
        from analysis.risk_engine import RiskEngine
        print("✅ RiskEngine imported")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_directional_signal() -> bool:
    """Test directional signal generation."""
    print("\n" + "=" * 70)
    print("TEST 2: Directional Signal Engine")
    print("=" * 70)
    
    try:
        from analysis.directional_signal import DirectionalSignalEngine
        import pandas as pd
        
        # Create mock data
        signal_engine = DirectionalSignalEngine()
        
        # Test RSI calculation
        prices = pd.Series([100, 101, 102, 101, 100, 99, 100, 101, 102, 103,
                           104, 103, 102, 101, 100, 99, 98, 99, 100, 101])
        rsi = signal_engine.compute_rsi(prices, period=14)
        
        print(f"✅ RSI calculated: {rsi:.1f}")
        
        if not (0 <= rsi <= 100):
            print(f"❌ RSI out of range: {rsi}")
            return False
        
        # Test PCR calculation
        option_data = {
            'Option_Type': ['CE', 'CE', 'CE', 'PE', 'PE', 'PE'],
            'OI': [100000, 150000, 80000, 120000, 110000, 90000],
            'Strike': [23000, 23100, 23200, 22900, 22800, 22700]
        }
        option_df = pd.DataFrame(option_data)
        pcr = signal_engine.compute_pcr(option_df)
        
        print(f"✅ PCR calculated: {pcr:.2f}")
        
        if not (0.3 < pcr < 3.0):
            print(f"❌ PCR out of typical range: {pcr}")
            return False
        
        # Test signal generation
        signal = signal_engine.generate_signal(prices, option_df)
        print(f"✅ Signal generated: {signal.signal} (confidence: {signal.confidence:.0f}%)")
        
        return True
    except Exception as e:
        print(f"❌ Signal engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_strategy_builder() -> bool:
    """Test strategy builder with premium handling."""
    print("\n" + "=" * 70)
    print("TEST 3: Strategy Builder (Premium Handling)")
    print("=" * 70)
    
    try:
        # NOTE: Using archived legacy version for this test
        sys.path.append('archive/legacy_v1.0')
        from strategy_builder_old import StrategyTemplate
        sys.path.remove('archive/legacy_v1.0')
        
        # Create a simple long call strategy
        strategy = StrategyTemplate("Test Long Call", spot=23000, dte=7)
        strategy.add_leg('CE', 23100, 'buy', 1)
        
        # Test payoff WITHOUT premium
        spot_range = np.linspace(22900, 23300, 50)
        payoff_no_premium = strategy.compute_payoff(spot_range)
        print(f"✅ Payoff without premium calculated")
        
        # Test payoff WITH premium
        entry_premiums = {('CE', 23100, 'buy'): 150}
        payoff_with_premium = strategy.compute_payoff(spot_range, entry_premiums=entry_premiums)
        
        print(f"✅ Payoff with premium calculated")
        
        # Verify premium reduces payoff
        if np.all(payoff_with_premium <= payoff_no_premium):
            print(f"✅ Premium correctly reduces payoff")
            print(f"   No premium max P&L: ₹{np.max(payoff_no_premium):.0f}")
            print(f"   With premium max P&L: ₹{np.max(payoff_with_premium):.0f}")
            return True
        else:
            print(f"❌ Premium not applied correctly")
            return False
            
    except Exception as e:
        print(f"❌ Strategy builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kelly_sizing() -> bool:
    """Test Kelly criterion with sample size adjustment."""
    print("\n" + "=" * 70)
    print("TEST 4: Kelly Sizing (Sample Adjustment)")
    print("=" * 70)
    
    try:
        from analysis.position_sizer import PositionSizer
        
        sizer = PositionSizer(account_size=100000, max_risk_pct=2.0)
        
        # Test with large sample
        kelly_large = sizer.kelly_fraction(
            win_rate=0.55,
            avg_rr=2.0,
            sample_size=100
        )
        print(f"✅ Kelly with 100 samples: {kelly_large['recommended_fraction']:.2%}")
        
        # Test with small sample
        kelly_small = sizer.kelly_fraction(
            win_rate=0.55,
            avg_rr=2.0,
            sample_size=30
        )
        print(f"✅ Kelly with 30 samples: {kelly_small['recommended_fraction']:.2%}")
        
        # Verify small sample gives MORE conservative result
        if kelly_small['recommended_fraction'] <= kelly_large['recommended_fraction']:
            print(f"✅ Small sample properly adjusts to {kelly_small['uncertainty_factor']:.1f}x uncertainty factor")
            
            if kelly_small['warnings']:
                print(f"✅ Warnings triggered for small sample:")
                for w in kelly_small['warnings']:
                    print(f"   {w}")
            return True
        else:
            print(f"❌ Small sample not more conservative than large sample")
            return False
            
    except Exception as e:
        print(f"❌ Kelly sizing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fat_tail_range() -> bool:
    """Test fat-tail aware range prediction."""
    print("\n" + "=" * 70)
    print("TEST 5: Fat-Tail Range Prediction")
    print("=" * 70)
    
    try:
        from analysis.range_predictor import RangePredictor
        
        # Create mock data
        option_data = {
            'Option_Type': ['CE', 'PE'],
            'Strike': [23000, 23000],
            'OI': [100000, 100000],
            'Volume': [50000, 50000]
        }
        option_df = pd.DataFrame(option_data)
        
        # Create mock OHLC
        np.random.seed(42)
        close_prices = 23000 + np.random.randn(60) * 100
        nifty_data = pd.DataFrame({
            'high': close_prices + 50,
            'low': close_prices - 50,
            'close': close_prices
        })
        
        predictor = RangePredictor(
            options_data=option_df,
            historical_nifty=nifty_data,
            current_vix=20.0,
            current_spot=23000
        )
        
        pred = predictor.predict_statistical()
        
        print(f"✅ Statistical range calculated: {pred['lower_range']:.0f} - {pred['upper_range']:.0f}")
        
        if 'fat_tail_lower' in pred and 'fat_tail_multiplier' in pred:
            print(f"✅ Fat-tail range calculated: {pred['fat_tail_lower']:.0f} - {pred['fat_tail_upper']:.0f}")
            print(f"✅ Fat-tail multiplier: {pred['fat_tail_multiplier']:.2f}x")
            
            # Verify fat-tail is wider
            normal_width = pred['upper_range'] - pred['lower_range']
            fat_tail_width = pred['fat_tail_upper'] - pred['fat_tail_lower']
            
            if fat_tail_width >= normal_width:
                print(f"✅ Fat-tail range ({fat_tail_width:.0f}) is wider than normal ({normal_width:.0f})")
                return True
            else:
                print(f"❌ Fat-tail range should be wider")
                return False
        else:
            print(f"❌ Fat-tail calculations missing")
            return False
            
    except Exception as e:
        print(f"❌ Fat-tail range test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_decision_validation() -> bool:
    """Test decision engine with signal validation."""
    print("\n" + "=" * 70)
    print("TEST 6: Decision Engine Signal Validation")
    print("=" * 70)
    
    try:
        from analysis.decision_engine import DecisionEngine
        from analysis.directional_signal import DirectionalSignal
        
        engine = DecisionEngine()
        
        # Create mock signal
        mock_signal = DirectionalSignal(
            signal="CALL_BUY",
            confidence=80.0,
            rsi=28.5,
            pcr=0.65,
            rsi_percentile=0.285,
            pcr_percentile=0.35,
            reasons=["Test signal"]
        )
        
        # Test validation
        result = engine.validate_with_directional_signal(
            directional_signal=mock_signal,
            strategy_type="LONG_CALL",
            vol_edge_score=0.20,
            risk_of_ruin=0.08
        )
        
        print(f"✅ Decision validation completed")
        print(f"   Allowed: {result['allowed']}")
        print(f"   Confidence: {result['confidence']}/100")
        print(f"   Signal: {result['signal']}")
        
        if result['allowed']:
            print(f"✅ Trade correctly approved for aligned signal+strategy")
            return True
        else:
            print(f"❌ Trade should be approved for CALL_BUY + LONG_CALL")
            return False
            
    except Exception as e:
        print(f"❌ Decision validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests() -> bool:
    """Run all validation tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "DIRECTIONAL ENGINE INTEGRATION TEST" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    
    tests = [
        ("Imports", test_imports),
        ("Directional Signal", test_directional_signal),
        ("Strategy Builder", test_strategy_builder),
        ("Kelly Sizing", test_kelly_sizing),
        ("Fat-Tail Range", test_fat_tail_range),
        ("Decision Validation", test_decision_validation)
    ]
    
    results = []
    for name, test_func in tests:
        results.append((name, test_func()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {name}")
    
    print("-" * 70)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your directional trading engine is ready to use.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

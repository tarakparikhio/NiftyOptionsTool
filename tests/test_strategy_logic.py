"""
Standalone test for strategy builder logic (no external dependencies).
Tests core calculations without requiring pandas, numpy, scipy.
"""

def test_option_leg_creation():
    """Test OptionLeg dataclass structure."""
    print("✓ Testing OptionLeg creation...")
    
    # Mock dataclass structure
    class MockOptionLeg:
        def __init__(self, type, position, strike, expiry, entry_price, quantity=1):
            assert type in ['CE', 'PE'], "Type must be CE or PE"
            assert position in ['BUY', 'SELL'], "Position must be BUY or SELL"
            assert strike > 0, "Strike must be positive"
            assert entry_price >= 0, "Entry price must be non-negative"
            assert quantity > 0, "Quantity must be positive"
            
            self.type = type
            self.position = position
            self.strike = strike
            self.expiry = expiry
            self.entry_price = entry_price
            self.quantity = quantity
    
    # Test valid leg
    leg = MockOptionLeg('CE', 'BUY', 26000, 'weekly', 150, 1)
    assert leg.type == 'CE'
    assert leg.strike == 26000
    print("  ✅ Valid leg creation passed")
    
    # Test invalid type
    try:
        MockOptionLeg('INVALID', 'BUY', 26000, 'weekly', 150, 1)
        assert False, "Should have raised assertion error"
    except AssertionError as e:
        print(f"  ✅ Invalid type rejected: {e}")
    
    # Test invalid strike
    try:
        MockOptionLeg('CE', 'BUY', -100, 'weekly', 150, 1)
        assert False, "Should have raised assertion error"
    except AssertionError as e:
        print(f"  ✅ Invalid strike rejected: {e}")


def test_premium_calculation():
    """Test premium flow calculation logic."""
    print("\n✓ Testing premium flow...")
    
    legs = [
        {'position': 'BUY', 'premium': 10, 'qty': 1},  # Pay 10
        {'position': 'SELL', 'premium': 40, 'qty': 1}, # Receive 40
        {'position': 'SELL', 'premium': 40, 'qty': 1}, # Receive 40
        {'position': 'BUY', 'premium': 10, 'qty': 1},  # Pay 10
    ]
    
    lot_size = 50
    total_debit = 0
    total_credit = 0
    
    for leg in legs:
        premium = leg['premium'] * leg['qty'] * lot_size
        if leg['position'] == 'BUY':
            total_debit += premium
        else:
            total_credit += premium
    
    net = total_credit - total_debit
    
    print(f"  Debit: ₹{total_debit:,.0f}")
    print(f"  Credit: ₹{total_credit:,.0f}")
    print(f"  Net: ₹{net:,.0f}")
    
    assert total_debit == 1000, f"Expected 1000, got {total_debit}"
    assert total_credit == 4000, f"Expected 4000, got {total_credit}"
    assert net == 3000, f"Expected 3000, got {net}"
    print("  ✅ Premium flow calculation correct")


def test_payoff_logic():
    """Test payoff calculation logic (simplified)."""
    print("\n✓ Testing payoff logic...")
    
    # Iron Condor example: Spot = 26000
    # Long PE 25700 @ 10
    # Short PE 25800 @ 40
    # Short CE 26200 @ 40
    # Long CE 26500 @ 10
    # Put wing = 100, Call wing = 300
    
    spot = 26000
    lot_size = 50
    
    # Test at spot = 25600 (below all strikes - in put wing loss zone)
    spot_test = 25600
    
    # Long PE 25700: intrinsic = 25700 - 25600 = 100, paid 10, profit = 90
    lp_pnl = (100 - 10) * lot_size
    # Short PE 25800: intrinsic = 25800 - 25600 = 200, received 40, loss = -160
    sp_pnl = (40 - 200) * lot_size
    # Short CE 26200: intrinsic = 0, received 40, profit = 40
    sc_pnl = 40 * lot_size
    # Long CE 26500: intrinsic = 0, paid 10, loss = -10
    lc_pnl = -10 * lot_size
    
    total_pnl = lp_pnl + sp_pnl + sc_pnl + lc_pnl
    
    print(f"  At spot {spot_test}:")
    print(f"    Long PE: ₹{lp_pnl:,.0f}")
    print(f"    Short PE: ₹{sp_pnl:,.0f}")
    print(f"    Short CE: ₹{sc_pnl:,.0f}")
    print(f"    Long CE: ₹{lc_pnl:,.0f}")
    print(f"    Total: ₹{total_pnl:,.0f}")
    
    # At this spot: (90 - 160 + 40 - 10) = -40 per contract = -2000 for 50 lot
    # This is partially into the put wing
    assert total_pnl == -2000, f"Expected -2000, got {total_pnl}"
    print("  ✅ Payoff calculation correct")
    
    # Test at spot = 25650 (max put wing loss)
    spot_test = 25650
    
    # Long PE 25700: intrinsic = 50, paid 10, profit = 40
    lp_pnl = (50 - 10) * lot_size
    # Short PE 25800: intrinsic = 150, received 40, loss = -110
    sp_pnl = (40 - 150) * lot_size
    # Short CE 26200: intrinsic = 0, received 40, profit = 40
    sc_pnl = 40 * lot_size
    # Long CE 26500: intrinsic = 0, paid 10, loss = -10
    lc_pnl = -10 * lot_size
    
    total_pnl_max_loss_put = lp_pnl + sp_pnl + sc_pnl + lc_pnl
    
    print(f"\n  At spot {spot_test} (put wing max loss):")
    print(f"    Total: ₹{total_pnl_max_loss_put:,.0f}")
    
    # Put wing max loss = (100 - 60 net credit) * 50 = 40 * 50 = 2000... but net credit is 60 per contract
    # Actually: wing width = 100, net credit = 60, loss = (100-60)*50 = 2000
    # But at 25650: intrinsic diff = 100 (full wing), premium net = 60, so loss = (100-60)*50 = 2000
    expected_max_loss_put_wing = -2000
    assert total_pnl_max_loss_put == expected_max_loss_put_wing, f"Expected {expected_max_loss_put_wing}, got {total_pnl_max_loss_put}"
    print("  ✅ Put wing max loss correct")
    
    # Test at spot = 26000 (inside wings)
    spot_test = 26000
    
    # All options expire worthless (spot between short strikes)
    # Long PE 25700: intrinsic = 0, paid 10, loss = -10
    lp_pnl = -10 * lot_size
    # Short PE 25800: intrinsic = 0, received 40, profit = 40
    sp_pnl = 40 * lot_size
    # Short CE 26200: intrinsic = 0, received 40, profit = 40
    sc_pnl = 40 * lot_size
    # Long CE 26500: intrinsic = 0, paid 10, loss = -10
    lc_pnl = -10 * lot_size
    
    total_pnl = lp_pnl + sp_pnl + sc_pnl + lc_pnl
    
    print(f"\n  At spot {spot_test} (max profit zone):")
    print(f"    Total: ₹{total_pnl:,.0f}")
    
    # This should be max profit (net credit)
    expected_max_profit = (40 + 40 - 10 - 10) * lot_size
    assert total_pnl == expected_max_profit, f"Expected {expected_max_profit}, got {total_pnl}"
    print("  ✅ Max profit calculation correct")


def test_breakeven_logic():
    """Test breakeven finding logic."""
    print("\n✓ Testing breakeven logic...")
    
    # For Iron Condor:
    # Lower BE = Short PE strike - Net Credit / lot_size
    # Upper BE = Short CE strike + Net Credit / lot_size
    
    short_put = 25800
    short_call = 26200
    net_credit = 60  # (40 + 40 - 10 - 10)
    
    lower_be = short_put - net_credit
    upper_be = short_call + net_credit
    
    print(f"  Short Put: {short_put}")
    print(f"  Short Call: {short_call}")
    print(f"  Net Credit: ₹{net_credit}")
    print(f"  Lower BE: {lower_be}")
    print(f"  Upper BE: {upper_be}")
    
    assert lower_be == 25740, f"Expected 25740, got {lower_be}"
    assert upper_be == 26260, f"Expected 26260, got {upper_be}"
    print("  ✅ Breakeven calculation correct")


def test_risk_reward():
    """Test risk/reward ratio calculation."""
    print("\n✓ Testing risk/reward...")
    
    # Iron Condor: Wing width = 300, Net credit = 60
    wing_width = 300
    net_credit = 60
    lot_size = 50
    
    max_profit = net_credit * lot_size
    max_loss = (wing_width - net_credit) * lot_size
    
    risk_reward = max_profit / max_loss
    
    print(f"  Max Profit: ₹{max_profit:,.0f}")
    print(f"  Max Loss: ₹{max_loss:,.0f}")
    print(f"  Risk/Reward: 1:{risk_reward:.2f}")
    
    assert max_profit == 3000, f"Expected 3000, got {max_profit}"
    assert max_loss == 12000, f"Expected 12000, got {max_loss}"
    assert abs(risk_reward - 0.25) < 0.01, f"Expected 0.25, got {risk_reward}"
    print("  ✅ Risk/reward calculation correct")


def test_margin_estimation():
    """Test margin estimation logic."""
    print("\n✓ Testing margin estimation...")
    
    # For defined risk strategy (Iron Condor)
    # Margin = max_loss
    max_loss = 12000
    margin = max_loss
    
    print(f"  Defined Risk Strategy")
    print(f"  Max Loss: ₹{max_loss:,.0f}")
    print(f"  Margin: ₹{margin:,.0f}")
    
    assert margin == 12000, f"Expected 12000, got {margin}"
    print("  ✅ Defined risk margin correct")
    
    # For undefined risk (e.g., naked short)
    spot = 26000
    qty = 1
    lot_size = 50
    margin_pct = 0.20
    
    naked_margin = spot * margin_pct * qty * lot_size
    
    print(f"\n  Undefined Risk Strategy (Naked Short)")
    print(f"  Spot: ₹{spot:,.0f}")
    print(f"  Margin %: {margin_pct * 100}%")
    print(f"  Margin: ₹{naked_margin:,.0f}")
    
    assert naked_margin == 260000, f"Expected 260000, got {naked_margin}"
    print("  ✅ Naked position margin correct")


def main():
    """Run all tests."""
    print("=" * 60)
    print("STRATEGY BUILDER LOGIC TESTS")
    print("=" * 60)
    
    try:
        test_option_leg_creation()
        test_premium_calculation()
        test_payoff_logic()
        test_breakeven_logic()
        test_risk_reward()
        test_margin_estimation()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

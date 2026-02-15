"""
Options Strategy Builder (Legacy - Deprecated)

⚠️ DEPRECATED: This module is kept for backward compatibility with:
   - analysis/directional_workflow.py (workflow example)
   - tests/test_directional_engine.py (integration tests)

For new code, use analysis/strategy_builder_v2.py which provides:
   - Strategy class (vs StrategyTemplate)
   - create_iron_condor(), create_strangle(), create_straddle() functions
   - Comprehensive risk metrics (POP, Greeks, margin estimation)
   - Professional UI components

Templates and backtesting for common option strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.stats import norm


class StrategyTemplate:
    """Base class for option strategy templates."""
    
    def __init__(self, name: str, spot: float, dte: int):
        """
        Initialize strategy template.
        
        Args:
            name: Strategy name
            spot: Current spot price
            dte: Days to expiry
        """
        self.name = name
        self.spot = spot
        self.dte = dte
        self.legs = []
        self.required_strikes = []
    
    def add_leg(self, option_type: str, strike: float, position: str, quantity: int = 1):
        """Add an option leg to the strategy."""
        self.legs.append({
            'type': option_type,
            'strike': strike,
            'position': position,
            'quantity': quantity
        })
    
    def compute_payoff(
        self, 
        spot_range: np.ndarray, 
        iv: float = None,
        entry_premiums: Optional[Dict[Tuple, float]] = None
    ) -> np.ndarray:
        """
        Compute strategy payoff across spot range at EXPIRY.
        
        ⚠️ IMPORTANT: This calculates intrinsic value at expiry.
        For pre-expiry mark-to-market P&L, use mark_to_market() instead.
        
        Args:
            spot_range: Array of spot prices
            iv: Implied volatility (%) - optional, used only for Greeks
            entry_premiums: Dict of {(option_type, strike, position): premium_paid}
                           For accounting debit/credit
                           Example: {('CE', 25300, 'buy'): 150}
            
        Returns:
            Array of payoffs at expiry (intrinsic value minus premiums)
        """
        payoff = np.zeros_like(spot_range)
        entry_premiums = entry_premiums or {}
        
        total_debit = 0.0
        total_credit = 0.0
        
        for leg in self.legs:
            option_type = leg['type']
            strike = leg['strike']
            position = leg['position']
            quantity = leg['quantity']
            
            # Intrinsic value at expiry
            if option_type == 'CE':
                leg_payoff = np.maximum(spot_range - strike, 0)
            else:  # PE
                leg_payoff = np.maximum(strike - spot_range, 0)
            
            # Apply position (buy = +1, sell = -1)
            multiplier = quantity if position == 'buy' else -quantity
            payoff += multiplier * leg_payoff
            
            # Track premiums
            key = (option_type, strike, position)
            if key in entry_premiums:
                premium = entry_premiums[key] * quantity
                if position == 'buy':
                    total_debit += premium
                else:
                    total_credit += premium
        
        # Net premium adjustment: subtract what you paid, add what you collected
        net_premium = total_debit - total_credit
        payoff = payoff - net_premium
        
        return payoff
    
    def get_breakevens(self, premium: float = 0) -> List[float]:
        """Calculate breakeven points."""
        # Simplified - would need actual premium data
        return []
    
    def get_max_profit(self) -> float:
        """Calculate maximum profit."""
        spot_range = np.linspace(self.spot * 0.8, self.spot * 1.2, 1000)
        payoff = self.compute_payoff(spot_range)
        return np.max(payoff)
    
    def get_max_loss(self) -> float:
        """Calculate maximum loss."""
        spot_range = np.linspace(self.spot * 0.8, self.spot * 1.2, 1000)
        payoff = self.compute_payoff(spot_range)
        return np.min(payoff)


class IronCondor(StrategyTemplate):
    """Iron Condor Strategy: Sell OTM call + put, protect with further OTM options."""
    
    def __init__(self, spot: float, dte: int, wing_width: int = 200):
        """
        Initialize Iron Condor.
        
        Args:
            spot: Current spot
            dte: Days to expiry
            wing_width: Distance between strikes
        """
        super().__init__("Iron Condor", spot, dte)
        
        # Determine strikes
        short_call_strike = round(spot + 200, -2)
        short_put_strike = round(spot - 200, -2)
        long_call_strike = short_call_strike + wing_width
        long_put_strike = short_put_strike - wing_width
        
        # Add legs
        self.add_leg('PE', long_put_strike, 'buy', 1)
        self.add_leg('PE', short_put_strike, 'sell', 1)
        self.add_leg('CE', short_call_strike, 'sell', 1)
        self.add_leg('CE', long_call_strike, 'buy', 1)
        
        self.required_strikes = [long_put_strike, short_put_strike, short_call_strike, long_call_strike]


class Strangle(StrategyTemplate):
    """Long Strangle: Buy OTM call + put expecting big move."""
    
    def __init__(self, spot: float, dte: int, delta_distance: int = 300):
        """
        Initialize Long Strangle.
        
        Args:
            spot: Current spot
            dte: Days to expiry
            delta_distance: Distance from spot for strikes
        """
        super().__init__("Long Strangle", spot, dte)
        
        call_strike = round(spot + delta_distance, -2)
        put_strike = round(spot - delta_distance, -2)
        
        self.add_leg('CE', call_strike, 'buy', 1)
        self.add_leg('PE', put_strike, 'buy', 1)
        
        self.required_strikes = [put_strike, call_strike]


class Straddle(StrategyTemplate):
    """Long Straddle: Buy ATM call + put expecting volatility."""
    
    def __init__(self, spot: float, dte: int):
        """Initialize Long Straddle."""
        super().__init__("Long Straddle", spot, dte)
        
        atm_strike = round(spot, -2)
        
        self.add_leg('CE', atm_strike, 'buy', 1)
        self.add_leg('PE', atm_strike, 'buy', 1)
        
        self.required_strikes = [atm_strike]


class BullCallSpread(StrategyTemplate):
    """Bull Call Spread: Buy lower call, sell higher call."""
    
    def __init__(self, spot: float, dte: int, spread_width: int = 200):
        """Initialize Bull Call Spread."""
        super().__init__("Bull Call Spread", spot, dte)
        
        lower_strike = round(spot, -2)
        higher_strike = lower_strike + spread_width
        
        self.add_leg('CE', lower_strike, 'buy', 1)
        self.add_leg('CE', higher_strike, 'sell', 1)
        
        self.required_strikes = [lower_strike, higher_strike]


class BearPutSpread(StrategyTemplate):
    """Bear Put Spread: Buy higher put, sell lower put."""
    
    def __init__(self, spot: float, dte: int, spread_width: int = 200):
        """Initialize Bear Put Spread."""
        super().__init__("Bear Put Spread", spot, dte)
        
        higher_strike = round(spot, -2)
        lower_strike = higher_strike - spread_width
        
        self.add_leg('PE', higher_strike, 'buy', 1)
        self.add_leg('PE', lower_strike, 'sell', 1)
        
        self.required_strikes = [lower_strike, higher_strike]


class CoveredCall(StrategyTemplate):
    """Covered Call: Own stock + sell OTM call."""
    
    def __init__(self, spot: float, dte: int, call_distance: int = 200):
        """Initialize Covered Call."""
        super().__init__("Covered Call", spot, dte)
        
        call_strike = round(spot + call_distance, -2)
        
        self.add_leg('CE', call_strike, 'sell', 1)
        
        self.required_strikes = [call_strike]


class CalendarSpread(StrategyTemplate):
    """Calendar Spread: Sell near-term, buy far-term at same strike."""
    
    def __init__(self, spot: float, near_dte: int, far_dte: int):
        """Initialize Calendar Spread."""
        super().__init__("Calendar Spread", spot, near_dte)
        
        atm_strike = round(spot, -2)
        
        # Note: Simplified - would need two expiry handling
        self.add_leg('CE', atm_strike, 'sell', 1)  # Near-term
        self.add_leg('CE', atm_strike, 'buy', 1)   # Far-term (different expiry)
        
        self.required_strikes = [atm_strike]


class StrategyBuilder:
    """
    Main builder for creating and analyzing option strategies.
    """
    
    def __init__(self, spot: float, dte: int):
        """
        Initialize strategy builder.
        
        Args:
            spot: Current spot price
            dte: Days to expiry
        """
        self.spot = spot
        self.dte = dte
    
    def create_strategy(self, strategy_name: str, **kwargs) -> Optional[StrategyTemplate]:
        """
        Create strategy by name.
        
        Args:
            strategy_name: Name of strategy
            **kwargs: Strategy-specific parameters
            
        Returns:
            Strategy template
        """
        strategies = {
            'iron_condor': IronCondor,
            'strangle': Strangle,
            'straddle': Straddle,
            'bull_call_spread': BullCallSpread,
            'bear_put_spread': BearPutSpread,
            'covered_call': CoveredCall,
            'calendar_spread': CalendarSpread
        }
        
        strategy_class = strategies.get(strategy_name.lower())
        if not strategy_class:
            return None
        
        return strategy_class(self.spot, self.dte, **kwargs)
    
    def analyze_strategy(self, strategy: StrategyTemplate, 
                        options_data: pd.DataFrame) -> Dict:
        """
        Analyze strategy with current OI and IV data.
        
        Args:
            strategy: Strategy template
            options_data: DataFrame with option chain
            
        Returns:
            Analysis results
        """
        analysis = {
            'strategy_name': strategy.name,
            'legs': strategy.legs,
            'max_profit': strategy.get_max_profit(),
            'max_loss': strategy.get_max_loss(),
            'strikes_analysis': []
        }
        
        # Check OI at required strikes
        for strike in strategy.required_strikes:
            strike_data = options_data[options_data['STRIKE'] == strike]
            
            if not strike_data.empty:
                analysis['strikes_analysis'].append({
                    'strike': strike,
                    'ce_oi': strike_data.iloc[0].get('CE_OI', 0),
                    'pe_oi': strike_data.iloc[0].get('PE_OI', 0),
                    'ce_iv': strike_data.iloc[0].get('CE_IV', 0),
                    'pe_iv': strike_data.iloc[0].get('PE_IV', 0)
                })
        
        return analysis
    
    def compute_pnl_profile(self, strategy: StrategyTemplate, 
                           spot_range: Optional[np.ndarray] = None) -> pd.DataFrame:
        """
        Compute P&L profile across spot range.
        
        Args:
            strategy: Strategy template
            spot_range: Range of spot prices (optional)
            
        Returns:
            DataFrame with spot and P&L
        """
        if spot_range is None:
            spot_range = np.linspace(self.spot * 0.85, self.spot * 1.15, 100)
        
        payoff = strategy.compute_payoff(spot_range)
        
        df = pd.DataFrame({
            'spot': spot_range,
            'pnl': payoff,
            'pnl_pct': (payoff / self.spot) * 100
        })
        
        return df
    
    def backtest_strategy(self, strategy: StrategyTemplate,
                         historical_data: List[pd.DataFrame]) -> Dict:
        """
        Backtest strategy on historical data.
        
        Args:
            strategy: Strategy template
            historical_data: List of historical option chain DataFrames
            
        Returns:
            Backtest results
        """
        results = {
            'total_trades': len(historical_data),
            'profitable_trades': 0,
            'total_pnl': 0,
            'win_rate': 0,
            'trades': []
        }
        
        for i, df in enumerate(historical_data):
            # Simplified backtesting logic
            # In reality, would need entry/exit prices, premium data
            
            # Check if strategy strikes exist in data
            trade_result = {
                'trade_num': i + 1,
                'simulated_pnl': 0  # Placeholder
            }
            
            results['trades'].append(trade_result)
        
        if results['total_trades'] > 0:
            results['win_rate'] = (results['profitable_trades'] / results['total_trades']) * 100
        
        return results
    
    def get_all_strategies(self) -> List[str]:
        """Get list of available strategies."""
        return [
            'iron_condor',
            'strangle',
            'straddle',
            'bull_call_spread',
            'bear_put_spread',
            'covered_call',
            'calendar_spread'
        ]
    
    def suggest_strategy(self, market_conditions: Dict) -> str:
        """
        Suggest strategy based on market conditions.
        
        Args:
            market_conditions: Dict with pcr, vix, trend, etc.
            
        Returns:
            Suggested strategy name
        """
        pcr = market_conditions.get('pcr', 1.0)
        vix = market_conditions.get('vix', 15)
        trend = market_conditions.get('trend', 'neutral')
        
        # High volatility
        if vix > 20:
            if pcr > 1.3:
                return 'iron_condor'  # Sell premium in range
            else:
                return 'strangle'  # Expect big move
        
        # Low volatility
        elif vix < 12:
            return 'straddle'  # Buy volatility
        
        # Directional
        elif trend == 'bullish':
            return 'bull_call_spread'
        elif trend == 'bearish':
            return 'bear_put_spread'
        
        # Neutral
        else:
            return 'iron_condor'


if __name__ == "__main__":
    # Test strategy builder
    builder = StrategyBuilder(spot=26000, dte=7)
    
    # Create Iron Condor
    ic = builder.create_strategy('iron_condor', wing_width=300)
    print(f"\n{ic.name}")
    print(f"Legs: {ic.legs}")
    print(f"Max Profit: {ic.get_max_profit():.2f}")
    print(f"Max Loss: {ic.get_max_loss():.2f}")
    
    # P&L Profile
    pnl_df = builder.compute_pnl_profile(ic)
    print(f"\nP&L at spot range:")
    print(pnl_df.head())
    
    # Strategy suggestion
    conditions = {'pcr': 1.45, 'vix': 19, 'trend': 'neutral'}
    suggested = builder.suggest_strategy(conditions)
    print(f"\nSuggested Strategy: {suggested}")

"""
Professional Options Strategy Builder - Sensibull-style
Comprehensive multi-leg strategy analysis with risk metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import date, datetime
from scipy.stats import norm
from scipy.optimize import brentq
import sys
sys.path.append('..')
from utils.greeks_calculator import GreeksCalculator


@dataclass
class OptionLeg:
    """Single option leg in a strategy."""
    type: str  # "CE" or "PE"
    position: str  # "BUY" or "SELL"
    strike: float
    expiry: Union[date, str]
    entry_price: float  # Premium paid/received
    quantity: int = 1
    
    def __post_init__(self):
        """Validate leg data."""
        assert self.type in ['CE', 'PE'], "Type must be CE or PE"
        assert self.position in ['BUY', 'SELL'], "Position must be BUY or SELL"
        assert self.strike > 0, "Strike must be positive"
        assert self.entry_price >= 0, "Entry price must be non-negative"
        assert self.quantity > 0, "Quantity must be positive"


@dataclass
class StrategyMetrics:
    """Comprehensive strategy risk metrics."""
    max_profit: Union[float, str]
    max_loss: Union[float, str]
    breakevens: List[float]
    net_credit: float
    net_debit: float
    pop: float  # Probability of profit
    risk_reward_ratio: float
    net_delta: float
    net_gamma: float
    net_theta: float
    net_vega: float
    estimated_margin: float
    strategy_type: str  # "CREDIT" or "DEBIT"


class Strategy:
    """
    Professional multi-leg options strategy with comprehensive analytics.
    """
    
    def __init__(self, name: str, spot_price: float, lot_size: int = 50):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
            spot_price: Current underlying spot price
            lot_size: Standard lot size (NIFTY = 50)
        """
        self.name = name
        self.spot_price = spot_price
        self.lot_size = lot_size
        self.legs: List[OptionLeg] = []
        self.greeks_calc = GreeksCalculator()
        
    def add_leg(self, leg: OptionLeg):
        """Add an option leg to the strategy."""
        self.legs.append(leg)
        
    def remove_leg(self, index: int):
        """Remove a leg by index."""
        if 0 <= index < len(self.legs):
            self.legs.pop(index)
            
    def get_net_premium(self) -> Tuple[float, float, float]:
        """
        Calculate net premium flow.
        
        Returns:
            (total_debit, total_credit, net_premium)
            Positive net = credit received
            Negative net = debit paid
        """
        total_debit = 0.0
        total_credit = 0.0
        
        for leg in self.legs:
            premium = leg.entry_price * leg.quantity * self.lot_size
            
            if leg.position == 'BUY':
                total_debit += premium
            else:  # SELL
                total_credit += premium
        
        net_premium = total_credit - total_debit
        
        return total_debit, total_credit, net_premium
    
    def compute_payoff_at_expiry(self, spot_prices: np.ndarray) -> np.ndarray:
        """
        Compute strategy P&L at expiry.
        
        Args:
            spot_prices: Array of spot prices to evaluate
            
        Returns:
            Array of P&L values (per position, not per lot)
        """
        payoff = np.zeros_like(spot_prices, dtype=float)
        
        for leg in self.legs:
            # Intrinsic value at expiry
            if leg.type == 'CE':
                intrinsic = np.maximum(spot_prices - leg.strike, 0)
            else:  # PE
                intrinsic = np.maximum(leg.strike - spot_prices, 0)
            
            # Leg P&L
            if leg.position == 'BUY':
                # Long option: Intrinsic - Premium paid
                leg_pnl = intrinsic - leg.entry_price
            else:  # SELL
                # Short option: Premium received - Intrinsic
                leg_pnl = leg.entry_price - intrinsic
            
            # Multiply by quantity and lot size
            payoff += leg_pnl * leg.quantity * self.lot_size
        
        return payoff
    
    def mark_to_market(self, spot: float, iv: float, dte: int) -> float:
        """
        Calculate current P&L using Black-Scholes.
        
        Args:
            spot: Current spot price
            iv: Current implied volatility (decimal, e.g., 0.15)
            dte: Days to expiry
            
        Returns:
            Current P&L
        """
        pnl = 0.0
        time_to_expiry = max(dte / 365, 0.001)
        
        for leg in self.legs:
            # Calculate current option price using BS
            greeks = self.greeks_calc.calculate_greeks(
                spot=spot,
                strike=leg.strike,
                time_to_expiry=time_to_expiry,
                volatility=iv,
                option_type=leg.type
            )
            
            # Estimate current option price (simplified)
            # In production, would use full BS pricing
            if leg.type == 'CE':
                intrinsic = max(spot - leg.strike, 0)
            else:
                intrinsic = max(leg.strike - spot, 0)
            
            time_value = greeks['Vega'] * iv * 100  # Rough estimate
            current_price = intrinsic + time_value
            
            # Leg P&L
            if leg.position == 'BUY':
                leg_pnl = current_price - leg.entry_price
            else:  # SELL
                leg_pnl = leg.entry_price - current_price
            
            pnl += leg_pnl * leg.quantity * self.lot_size
        
        return pnl
    
    def calculate_breakevens(self) -> List[float]:
        """
        Calculate breakeven points by solving P&L = 0.
        
        Returns:
            List of breakeven spot prices
        """
        breakevens = []
        
        # Sample P&L across range
        spot_range = np.linspace(self.spot_price * 0.5, self.spot_price * 1.5, 1000)
        payoff = self.compute_payoff_at_expiry(spot_range)
        
        # Find zero crossings
        sign_changes = np.where(np.diff(np.sign(payoff)))[0]
        
        for idx in sign_changes:
            # Refine using root finding
            try:
                def pnl_func(spot):
                    return float(self.compute_payoff_at_expiry(np.array([spot]))[0])
                
                be = brentq(pnl_func, spot_range[idx], spot_range[idx + 1])
                breakevens.append(round(be, 2))
            except:
                # If root finding fails, use interpolation
                x1, x2 = spot_range[idx], spot_range[idx + 1]
                y1, y2 = payoff[idx], payoff[idx + 1]
                be = x1 - y1 * (x2 - x1) / (y2 - y1)
                breakevens.append(round(be, 2))
        
        return sorted(list(set(breakevens)))
    
    def calculate_max_profit_loss(self) -> Tuple[Union[float, str], Union[float, str]]:
        """
        Calculate maximum profit and loss.
        
        Returns:
            (max_profit, max_loss) - may be "Unlimited"        """
        spot_range = np.linspace(self.spot_price * 0.5, self.spot_price * 1.5, 2000)
        payoff = self.compute_payoff_at_expiry(spot_range)
        
        max_profit = np.max(payoff)
        max_loss = np.min(payoff)
        
        # Check for unlimited scenarios
        # If payoff keeps increasing at edges, it's unlimited
        if payoff[-1] > payoff[-100]:  # Growing at upper end
            if payoff[-1] - payoff[-100] > self.spot_price * 0.1:
                max_profit = "Unlimited"
        
        if payoff[0] < payoff[100]:  # Growing (more negative) at lower end
            if abs(payoff[0] - payoff[100]) > self.spot_price * 0.1:
                max_loss = "Unlimited"
        
        # Round if numeric
        if isinstance(max_profit, float):
            max_profit = round(max_profit, 2)
        if isinstance(max_loss, float):
            max_loss = round(max_loss, 2)
        
        return max_profit, max_loss
    
    def aggregate_greeks(self, iv: float, dte: int) -> Dict[str, float]:
        """
        Calculate net Greeks for entire strategy.
        
        Args:
            iv: Implied volatility (decimal)
            dte: Days to expiry
            
        Returns:
            Dictionary of net Greeks
        """
        net_greeks = {
            'Delta': 0.0,
            'Gamma': 0.0,
            'Theta': 0.0,
            'Vega': 0.0
        }
        
        time_to_expiry = max(dte / 365, 0.001)
        
        for leg in self.legs:
            greeks = self.greeks_calc.calculate_greeks(
                spot=self.spot_price,
                strike=leg.strike,
                time_to_expiry=time_to_expiry,
                volatility=iv,
                option_type=leg.type
            )
            
            # Apply position multiplier
            multiplier = leg.quantity * self.lot_size
            if leg.position == 'SELL':
                multiplier *= -1
            
            for greek_name in net_greeks:
                net_greeks[greek_name] += greeks[greek_name] * multiplier
        
        return net_greeks
    
    def estimate_margin(self) -> float:
        """
        Estimate margin requirement (SPAN-like approximation).
        
        Returns:
            Estimated margin in ₹
        """
        margin = 0.0
        
        # For spreads: margin = max loss
        max_profit, max_loss = self.calculate_max_profit_loss()
        
        if isinstance(max_loss, float) and max_loss < 0:
            # Defined risk strategy
            margin = abs(max_loss)
        else:
            # Undefined risk - use percentage of underlying
            for leg in self.legs:
                if leg.position == 'SELL':
                    # Naked short: ~20% of underlying value
                    leg_margin = self.spot_price * 0.20 * leg.quantity * self.lot_size
                    margin += leg_margin
        
        return round(margin, 2)
    
    def calculate_pop(self, iv: float, dte: int) -> float:
        """
        Calculate Probability of Profit using lognormal distribution.
        
        Args:
            iv: ATM implied volatility (decimal)
            dte: Days to expiry
            
        Returns:
            Probability of profit (0-1)
        """
        if dte <= 0:
            # At expiry: check if current spot is profitable
            current_pnl = self.compute_payoff_at_expiry(np.array([self.spot_price]))[0]
            return 1.0 if current_pnl > 0 else 0.0
        
        # Find profit zones
        breakevens = self.calculate_breakevens()
        
        if not breakevens:
            # No breakevens found - check if always profitable or always losing
            sample_pnl = self.compute_payoff_at_expiry(np.array([self.spot_price]))[0]
            return 1.0 if sample_pnl > 0 else 0.0
        
        # Calculate expected move
        time_to_expiry = dte / 365
        std_dev = self.spot_price * iv * np.sqrt(time_to_expiry)
        
        # Sample probabilities across spot range
        spot_range = np.linspace(
            self.spot_price - 4 * std_dev,
            self.spot_price + 4 * std_dev,
            1000
        )
        
        # Lognormal distribution probabilities
        # d2 from Black-Scholes
        mu = np.log(self.spot_price) + (-0.5 * iv**2) * time_to_expiry
        sigma = iv * np.sqrt(time_to_expiry)
        
        log_prices = np.log(spot_range)
        prob_density = norm.pdf(log_prices, mu, sigma) / spot_range
        prob_density /= prob_density.sum()  # Normalize
        
        # Calculate P&L at each spot
        payoff = self.compute_payoff_at_expiry(spot_range)
        
        # POP = sum of probabilities where P&L > 0
        pop = np.sum(prob_density[payoff > 0])
        
        return round(float(pop), 4)
    
    def get_comprehensive_metrics(self, iv: float, dte: int) -> StrategyMetrics:
        """
        Get all strategy metrics in one call.
        
        Args:
            iv: ATM implied volatility (decimal)
            dte: Days to expiry
            
        Returns:
            StrategyMetrics object
        """
        max_profit, max_loss = self.calculate_max_profit_loss()
        breakevens = self.calculate_breakevens()
        total_debit, total_credit, net_premium = self.get_net_premium()
        pop = self.calculate_pop(iv, dte)
        greeks = self.aggregate_greeks(iv, dte)
        margin = self.estimate_margin()
        
        # Calculate risk/reward ratio
        if isinstance(max_profit, float) and isinstance(max_loss, float):
            if max_loss != 0:
                rr_ratio = abs(max_profit / max_loss)
            else:
                rr_ratio = float('inf')
        else:
            rr_ratio = float('inf')
        
        # Strategy type
        strategy_type = "CREDIT" if net_premium > 0 else "DEBIT"
        
        return StrategyMetrics(
            max_profit=max_profit,
            max_loss=max_loss,
            breakevens=breakevens,
            net_credit=total_credit,
            net_debit=total_debit,
            pop=pop,
            risk_reward_ratio=round(rr_ratio, 2),
            net_delta=round(greeks['Delta'], 2),
            net_gamma=round(greeks['Gamma'], 4),
            net_theta=round(greeks['Theta'], 2),
            net_vega=round(greeks['Vega'], 2),
            estimated_margin=margin,
            strategy_type=strategy_type
        )


class StrikeSuggestionEngine:
    """Suggest strikes based on Greeks and deltas."""
    
    def __init__(self, options_data: pd.DataFrame, spot: float):
        """
        Initialize strike suggester.
        
        Args:
            options_data: Options chain with strikes, premiums, IVs
            spot: Current spot price
        """
        self.options_data = options_data
        self.spot = spot
        self.greeks_calc = GreeksCalculator()
    
    def suggest_strike(self, 
                      direction: str,
                      delta_range: Tuple[float, float] = (0.4, 0.6),
                      option_type: str = None,
                      dte: int = 7) -> Dict:
        """
        Suggest optimal strike based on delta range.
        
        Args:
            direction: "CALL_BUY", "PUT_BUY", "CALL_SELL", "PUT_SELL"
            delta_range: Target delta range (e.g., (0.4, 0.6))
            option_type: Override option type
            dte: Days to expiry
            
        Returns:
            Dict with strike, delta, premium, iv
        """
        # Determine option type from direction
        if option_type is None:
            if 'CALL' in direction.upper():
                option_type = 'CE'
            else:
                option_type = 'PE'
        
        time_to_expiry = dte / 365
        candidates = []
        
        # Filter options data
        if 'Option_Type' in self.options_data.columns:
            filtered_df = self.options_data[
                self.options_data['Option_Type'] == option_type
            ].copy()
        else:
            filtered_df = self.options_data.copy()
        
        for _, row in filtered_df.iterrows():
            strike = row.get('Strike', row.get('STRIKE'))
            if pd.isna(strike):
                continue
            
            # Get IV
            if option_type == 'CE':
                iv = row.get('CE_IV', row.get('IV', 15)) / 100
                premium = row.get('CE_LTP', row.get('LTP', 0))
            else:
                iv = row.get('PE_IV', row.get('IV', 15)) / 100
                premium = row.get('PE_LTP', row.get('LTP', 0))
            
            if iv <= 0:
                iv = 0.15  # Default
            
            # Calculate Greeks
            try:
                greeks = self.greeks_calc.calculate_greeks(
                    spot=self.spot,
                    strike=strike,
                    time_to_expiry=time_to_expiry,
                    volatility=iv,
                    option_type=option_type
                )
                
                delta = abs(greeks['Delta'])
                
                # Check if delta in range
                if delta_range[0] <= delta <= delta_range[1]:
                    candidates.append({
                        'strike': strike,
                        'delta': round(delta, 3),
                        'premium': premium,
                        'iv': round(iv * 100, 2),
                        'distance_from_atm': abs(strike - self.spot)
                    })
            except:
                continue
        
        if not candidates:
            # No candidates - return closest to ATM
            filtered_df['distance'] = abs(filtered_df['Strike'] - self.spot)
            closest = filtered_df.nsmallest(1, 'distance')
            
            if not closest.empty:
                row = closest.iloc[0]
                return {
                    'strike': row['Strike'],
                    'delta': 0.5,  # Estimate
                    'premium': row.get('CE_LTP' if option_type == 'CE' else 'PE_LTP', 0),
                    'iv': 15.0,
                    'distance_from_atm': abs(row['Strike'] - self.spot)
                }
            else:
                return None
        
        # Return closest to ATM with target delta
        candidates.sort(key=lambda x: x['distance_from_atm'])
        return candidates[0]


# Preset strategy templates
def create_iron_condor(spot: float, wing_width: int = 200, 
                      premiums: Dict = None, lot_size: int = 50) -> Strategy:
    """Create Iron Condor strategy."""
    strategy = Strategy("Iron Condor", spot, lot_size)
    
    short_call_strike = round(spot + 200, -2)
    short_put_strike = round(spot - 200, -2)
    long_call_strike = short_call_strike + wing_width
    long_put_strike = short_put_strike - wing_width
    
    # Default premiums if not provided
    if premiums is None:
        premiums = {
            long_put_strike: {'PE': 10},
            short_put_strike: {'PE': 40},
            short_call_strike: {'CE': 40},
            long_call_strike: {'CE': 10}
        }
    
    strategy.add_leg(OptionLeg('PE', 'BUY', long_put_strike, 'weekly', 
                               premiums.get(long_put_strike, {}).get('PE', 10), 1))
    strategy.add_leg(OptionLeg('PE', 'SELL', short_put_strike, 'weekly',
                               premiums.get(short_put_strike, {}).get('PE', 40), 1))
    strategy.add_leg(OptionLeg('CE', 'SELL', short_call_strike, 'weekly',
                               premiums.get(short_call_strike, {}).get('CE', 40), 1))
    strategy.add_leg(OptionLeg('CE', 'BUY', long_call_strike, 'weekly',
                               premiums.get(long_call_strike, {}).get('CE', 10), 1))
    
    return strategy


def create_strangle(spot: float, distance: int = 300,
                   premiums: Dict = None, lot_size: int = 50) -> Strategy:
    """Create Long Strangle strategy."""
    strategy = Strategy("Long Strangle", spot, lot_size)
    
    call_strike = round(spot + distance, -2)
    put_strike = round(spot - distance, -2)
    
    if premiums is None:
        premiums = {
            call_strike: {'CE': 50},
            put_strike: {'PE': 50}
        }
    
    strategy.add_leg(OptionLeg('CE', 'BUY', call_strike, 'weekly',
                               premiums.get(call_strike, {}).get('CE', 50), 1))
    strategy.add_leg(OptionLeg('PE', 'BUY', put_strike, 'weekly',
                               premiums.get(put_strike, {}).get('PE', 50), 1))
    
    return strategy


if __name__ == "__main__":
    # Example usage
    print("=== Professional Strategy Builder Demo ===\n")
    
    # Create Iron Condor
    spot = 26000
    ic = create_iron_condor(spot, wing_width=300)
    
    # Get comprehensive metrics
    metrics = ic.get_comprehensive_metrics(iv=0.15, dte=7)
    
    print(f"Strategy: {ic.name}")
    print(f"Spot: ₹{spot:,.0f}")
    print(f"\nLegs:")
    for i, leg in enumerate(ic.legs, 1):
        print(f"  {i}. {leg.position} {leg.quantity}x {leg.type} {leg.strike} @ ₹{leg.entry_price}")
    
    print(f"\n📊 Risk Metrics:")
    print(f"  Max Profit: ₹{metrics.max_profit:,.2f}" if isinstance(metrics.max_profit, float) else f"  Max Profit: {metrics.max_profit}")
    print(f"  Max Loss: ₹{abs(metrics.max_loss):,.2f}" if isinstance(metrics.max_loss, float) else f"  Max Loss: {metrics.max_loss}")
    print(f"  Breakevens: {[f'₹{be:,.0f}' for be in metrics.breakevens]}")
    print(f"  POP: {metrics.pop * 100:.1f}%")
    print(f"  Risk/Reward: 1:{metrics.risk_reward_ratio:.2f}")
    print(f"  Strategy Type: {metrics.strategy_type}")
    
    print(f"\n💰 Premium Flow:")
    print(f"  Credit: ₹{metrics.net_credit:,.2f}")
    print(f"  Debit: ₹{metrics.net_debit:,.2f}")
    print(f"  Net: ₹{metrics.net_credit - metrics.net_debit:,.2f}")
    
    print(f"\n📈 Greeks:")
    print(f"  Delta: {metrics.net_delta:.2f}")
    print(f"  Gamma: {metrics.net_gamma:.4f}")
    print(f"  Theta: {metrics.net_theta:.2f}")
    print(f"  Vega: {metrics.net_vega:.2f}")
    
    print(f"\n💳 Margin: ₹{metrics.estimated_margin:,.2f}")

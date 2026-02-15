"""
Position Sizer - Dynamic position sizing based on Kelly, fixed fraction, and volatility
"""
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PositionSizeOutput:
    """Output from position sizing calculation"""
    recommended_size: float
    capital_at_risk: float
    num_lots: int
    risk_pct: float
    method: str
    warnings: list
    kelly_detail: Optional[Dict] = None  # Sample size adjustment info


class PositionSizer:
    """
    Dynamic position sizing for options strategies.
    
    Methods:
    - Kelly Criterion (optimal growth)
    - Fixed Fraction (% risk)
    - Volatility Adjusted (dynamic based on VIX/IV)
    """
    
    def __init__(
        self,
        account_size: float = 100000.0,
        max_risk_pct: float = 3.0,
        lot_size: int = 50
    ):
        """
        Initialize Position Sizer.
        
        Args:
            account_size: Total account equity
            max_risk_pct: Maximum % of account to risk per trade (safety cap)
            lot_size: NIFTY lot size (currently 50)
        """
        self.account_size = account_size
        self.max_risk_pct = max_risk_pct / 100  # Convert to decimal
        self.lot_size = lot_size
    
    def kelly_fraction(
        self,
        win_rate: float,
        avg_rr: float,
        sample_size: int = 100,
        safety_factor: float = 0.25
    ) -> Dict[str, Any]:
        """
        Calculate Kelly Criterion position size with sample size adjustment.
        
        ⚠️ CRITICAL: Accounts for estimation error in win_rate.
        
        Kelly% = (p*b - q) / b
        where:
        - p = win rate
        - q = loss rate (1-p)
        - b = reward/risk ratio
        
        Args:
            win_rate: Probability of winning (0-1)
            avg_rr: Average risk-reward ratio
            sample_size: Number of trades used to calculate win_rate
            safety_factor: Fraction of Kelly to use (0.25 = quarter Kelly)
            
        Returns:
            Dict with:
            - recommended_fraction: Float, safe Kelly fraction to use
            - capital_at_risk: $ amount per trade
            - uncertainty_factor: Adjustment for sample size
            - warnings: List of cautions
        """
        warnings = []
        
        if avg_rr <= 0:
            return {
                'recommended_fraction': 0.0,
                'capital_at_risk': 0.0,
                'uncertainty_factor': 0.0,
                'warnings': ['avg_rr <= 0: Cannot calculate Kelly']
            }
        
        win_rate = np.clip(win_rate, 0.01, 0.99)
        loss_rate = 1 - win_rate
        
        # ⚠️ SAMPLE SIZE ADJUSTMENT
        # With sample_size < 100, win_rate has significant estimation error
        # Reduce position size accordingly
        uncertainty_factor = min(1.0, sample_size / 100)
        
        if sample_size < 50:
            warnings.append(
                f'⚠️ Sample size ({sample_size}) < 50: '
                'Win rate estimate unreliable. Using aggressive cap.'
            )
            uncertainty_factor = sample_size / 200  # Even more conservative
        
        # Kelly formula
        kelly = (win_rate * avg_rr - loss_rate) / avg_rr
        
        # Can't be negative
        kelly = max(0, kelly)
        
        # Apply safety factor (typically 1/4 Kelly = quarter Kelly)
        safe_kelly = kelly * safety_factor
        
        # Apply sample size uncertainty
        safe_kelly = safe_kelly * uncertainty_factor
        
        # Hard cap at max risk per trade
        recommended_risk = min(safe_kelly, self.max_risk_pct)
        
        # Calculate $ amount
        capital_at_risk = self.account_size * recommended_risk
        
        return {
            'recommended_fraction': recommended_risk,
            'capital_at_risk': capital_at_risk,
            'uncertainty_factor': uncertainty_factor,
            'full_kelly': kelly,
            'safe_kelly_before_adjustment': kelly * safety_factor,
            'warnings': warnings
        }
    
    def fixed_fraction(
        self,
        risk_percent: float
    ) -> float:
        """
        Simple fixed fraction position sizing.
        
        Args:
            risk_percent: Percentage of account to risk (e.g., 2.0 for 2%)
            
        Returns:
            Fraction of capital to risk
        """
        risk_fraction = risk_percent / 100
        return min(risk_fraction, self.max_risk_pct)
    
    def volatility_adjusted_size(
        self,
        base_risk: float,
        current_volatility: float,
        baseline_volatility: float = 15.0
    ) -> float:
        """
        Adjust position size based on volatility regime.
        
        Higher volatility = smaller size
        Lower volatility = larger size
        
        Args:
            base_risk: Base risk percentage
            current_volatility: Current IV or VIX (%)
            baseline_volatility: Normal volatility level (%)
            
        Returns:
            Adjusted risk fraction
        """
        if current_volatility <= 0 or baseline_volatility <= 0:
            return base_risk / 100
        
        # Volatility ratio
        vol_ratio = baseline_volatility / current_volatility
        
        # Adjust size (clamp between 0.5x and 1.5x)
        vol_ratio = np.clip(vol_ratio, 0.5, 1.5)
        
        # Adjusted risk
        adjusted_risk = (base_risk / 100) * vol_ratio
        
        # Cap at max
        adjusted_risk = min(adjusted_risk, self.max_risk_pct)
        
        return adjusted_risk
    
    def calculate_position_size(
        self,
        strategy: Dict[str, Any],
        win_rate: Optional[float] = None,
        avg_rr: Optional[float] = None,
        method: str = "fixed",
        risk_percent: float = 2.0,
        current_volatility: Optional[float] = None,
        sample_size: int = 100
    ) -> PositionSizeOutput:
        """
        Calculate recommended position size for a strategy.
        
        Args:
            strategy: Strategy dict with max_profit, max_loss
            win_rate: Historical win rate (for Kelly)
            avg_rr: Average risk-reward ratio (for Kelly)
            method: "kelly", "fixed", or "volatility_adjusted"
            risk_percent: Base risk % for fixed/volatility methods
            current_volatility: Current IV/VIX for volatility adjustment
            sample_size: Number of historical trades (for Kelly adjustment)
            
        Returns:
            PositionSizeOutput with recommended size and metrics
        """
        max_loss = abs(strategy.get('max_loss', 0))
        max_profit = strategy.get('max_profit', 0)
        
        warnings = []
        kelly_detail = None
        
        # Validation
        if max_loss == 0:
            return PositionSizeOutput(
                recommended_size=0,
                capital_at_risk=0,
                num_lots=0,
                risk_pct=0,
                method=method,
                warnings=["Cannot size: max loss is zero"],
                kelly_detail=None
            )
        
        # Calculate risk-reward if not provided
        if avg_rr is None and max_loss > 0:
            avg_rr = max_profit / max_loss
        
        # Determine risk fraction based on method
        risk_fraction = 0.0
        if method == "kelly" and win_rate is not None and avg_rr is not None:
            kelly_result = self.kelly_fraction(win_rate, avg_rr, sample_size=sample_size, safety_factor=0.25)
            risk_fraction = kelly_result.get('recommended_fraction', 0.0)
            kelly_detail = {
                'sample_size': sample_size,
                'base_fraction': kelly_result.get('full_kelly', 0),
                'adjusted_fraction': kelly_result.get('safe_kelly_before_adjustment', 0),
                'uncertainty_factor': kelly_result.get('uncertainty_factor', 1.0)
            }
            warnings.extend(kelly_result.get('warnings', []))
            
            if risk_fraction == 0:
                warnings.append("Kelly fraction is zero - no edge detected")
            
        elif method == "volatility_adjusted" and current_volatility is not None:
            risk_fraction = self.volatility_adjusted_size(
                base_risk=risk_percent,
                current_volatility=current_volatility,
                baseline_volatility=15.0
            )
            
            if current_volatility > 25:
                warnings.append(f"High volatility: {current_volatility:.1f}% - size reduced")
            
        else:  # Fixed fraction (default)
            risk_fraction = self.fixed_fraction(risk_percent)
        
        # Calculate position size
        capital_to_risk = self.account_size * risk_fraction
        
        # How much capital needed for this strategy position
        # Position size = capital_to_risk / max_loss_per_unit
        # For options: if max loss = ₹5000 per lot, and we want to risk ₹2000 total,
        # we can afford 2000/5000 = 0.4 lots → round down to 0 or up to 1
        
        position_capital = capital_to_risk
        
        # If max loss is per lot, calculate number of lots
        # Assume max_loss is already per lot from strategy builder
        if max_loss > 0:
            affordable_lots = capital_to_risk / max_loss
            num_lots = max(1, int(affordable_lots))  # At least 1 lot
        else:
            num_lots = 1
        
        # Actual capital at risk with discrete lots
        actual_capital_at_risk = num_lots * max_loss
        actual_risk_pct = (actual_capital_at_risk / self.account_size) * 100
        
        # Safety checks
        if actual_risk_pct > self.max_risk_pct * 100:
            warnings.append(f"Risk exceeds max: {actual_risk_pct:.2f}% > {self.max_risk_pct*100:.1f}%")
            # Reduce lots
            num_lots = max(1, int((self.max_risk_pct * self.account_size) / max_loss))
            actual_capital_at_risk = num_lots * max_loss
            actual_risk_pct = (actual_capital_at_risk / self.account_size) * 100
        
        if num_lots > 10:
            warnings.append(f"Large position: {num_lots} lots")
        
        # Recommended position size (in rupees)
        recommended_size = num_lots * max_loss
        
        return PositionSizeOutput(
            recommended_size=round(recommended_size, 2),
            capital_at_risk=round(actual_capital_at_risk, 2),
            num_lots=num_lots,
            risk_pct=round(actual_risk_pct, 2),
            method=method,
            warnings=warnings,
            kelly_detail=kelly_detail
        )
    
    def compare_sizing_methods(
        self,
        strategy: Dict[str, Any],
        win_rate: float,
        avg_rr: float,
        current_volatility: float = 18.0,
        base_risk_pct: float = 2.0,
        sample_size: int = 100
    ) -> Dict[str, PositionSizeOutput]:
        """
        Compare all sizing methods side by side.
        
        Args:
            strategy: Strategy definition
            win_rate: Historical win rate
            avg_rr: Risk-reward ratio
            current_volatility: Current IV/VIX
            base_risk_pct: Base risk for fixed/vol methods
            sample_size: Number of historical trades
            
        Returns:
            dict with results from each method
        """
        results = {}
        
        # Kelly
        results['kelly'] = self.calculate_position_size(
            strategy=strategy,
            win_rate=win_rate,
            avg_rr=avg_rr,
            method="kelly",
            sample_size=sample_size
        )
        
        # Fixed Fraction
        results['fixed'] = self.calculate_position_size(
            strategy=strategy,
            method="fixed",
            risk_percent=base_risk_pct
        )
        
        # Volatility Adjusted
        results['volatility_adjusted'] = self.calculate_position_size(
            strategy=strategy,
            method="volatility_adjusted",
            risk_percent=base_risk_pct,
            current_volatility=current_volatility
        )
        
        return results
    
    def update_account_size(self, new_size: float):
        """Update account size (e.g., after win/loss)"""
        self.account_size = new_size
    
    def get_risk_ladder(
        self,
        strategy: Dict[str, Any],
        risk_levels: Optional[list] = None
    ) -> Dict[float, PositionSizeOutput]:
        """
        Generate position sizes for different risk levels.
        
        Useful for scenario planning.
        
        Args:
            strategy: Strategy definition
            risk_levels: List of risk %s (default: [1, 2, 3, 5])
            
        Returns:
            dict mapping risk_pct to PositionSizeOutput
        """
        if risk_levels is None:
            risk_levels = [1.0, 2.0, 3.0, 5.0]
        
        ladder = {}
        for risk_pct in risk_levels:
            result = self.calculate_position_size(
                strategy=strategy,
                method="fixed",
                risk_percent=risk_pct
            )
            ladder[risk_pct] = result
        
        return ladder


def optimal_f(
    trades_history: list,
    starting_capital: float = 100000.0
) -> Dict[str, Any]:
    """
    Calculate Optimal F (Ralph Vince method).
    
    Finds the fraction that maximizes geometric growth based on actual trade history.
    Note: This is computationally intensive for large histories.
    
    Args:
        trades_history: List of trade P&Ls in rupees
        starting_capital: Starting account size
        
    Returns:
        dict with optimal fraction and analysis
    """
    if len(trades_history) < 10:
        return {
            'optimal_f': 0.0,
            'error': 'Need at least 10 trades for meaningful calculation'
        }
    
    # Convert to numpy array
    trades = np.array(trades_history)
    
    # Find largest loss (for normalization)
    largest_loss = abs(np.min(trades))
    
    if largest_loss == 0:
        return {
            'optimal_f': 0.0,
            'error': 'No losses in history'
        }
    
    # Test different fractions
    fractions = np.linspace(0.01, 0.5, 50)
    terminal_wealth = []
    
    for f in fractions:
        # Simulate geometric growth
        wealth = starting_capital
        for trade in trades:
            # Position size based on f and largest loss
            units = (f * wealth) / largest_loss
            # New wealth
            wealth += units * trade
            
            if wealth <= 0:
                wealth = 0
                break
        
        terminal_wealth.append(wealth)
    
    # Find optimal f
    optimal_idx = np.argmax(terminal_wealth)
    optimal_fraction = fractions[optimal_idx]
    max_wealth = terminal_wealth[optimal_idx]
    
    return {
        'optimal_f': round(optimal_fraction, 3),
        'expected_terminal_wealth': round(max_wealth, 2),
        'interpretation': f"Optimal position fraction: {optimal_fraction*100:.1f}% of largest loss"
    }


def risk_parity_sizing(
    strategies: list,
    volatilities: list
) -> Dict[str, float]:
    """
    Risk parity allocation across multiple strategies.
    
    Allocate inversely proportional to volatility.
    
    Args:
        strategies: List of strategy dicts
        volatilities: List of volatilities for each strategy
        
    Returns:
        dict mapping strategy index to allocation %
    """
    if len(strategies) != len(volatilities):
        raise ValueError("Strategies and volatilities must have same length")
    
    # Inverse volatilities
    inv_vols = [1/v for v in volatilities]
    total_inv_vol = sum(inv_vols)
    
    # Allocations
    allocations = {
        i: (inv_vol / total_inv_vol) * 100
        for i, inv_vol in enumerate(inv_vols)
    }
    
    return allocations

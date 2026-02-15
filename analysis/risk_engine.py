"""
Risk Engine - Monte Carlo simulation and risk of ruin analysis
Uses vectorized numpy for fast simulation (<2 seconds)
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SimulationParams:
    """Parameters for Monte Carlo simulation"""
    win_rate: float  # 0.0 to 1.0
    avg_rr: float  # Average risk-reward ratio
    risk_per_trade: float  # % of capital per trade
    num_simulations: int = 1000
    num_trades: int = 200
    starting_capital: float = 100000.0


class RiskEngine:
    """
    Monte Carlo equity simulation and risk metrics.
    
    Features:
    - Vectorized simulations (no loops)
    - Risk of ruin calculation
    - Drawdown analysis
    - Percentile outcomes
    """
    
    def __init__(self):
        """Initialize Risk Engine"""
        self.last_simulation = None
    
    def simulate_equity_paths(
        self,
        win_rate: float,
        avg_rr: float,
        risk_per_trade: float = 0.02,
        num_simulations: int = 1000,
        num_trades: int = 200,
        starting_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Run vectorized Monte Carlo equity simulation.
        
        Performance requirement: < 2 seconds for 1000 simulations x 200 trades.
        
        Args:
            win_rate: Probability of winning (0.0 to 1.0)
            avg_rr: Average risk-reward ratio (e.g., 2.0 = win 2x what you risk)
            risk_per_trade: Fraction of capital risked per trade (e.g., 0.02 = 2%)
            num_simulations: Number of equity paths to simulate
            num_trades: Number of trades in each path
            starting_capital: Initial account size
            
        Returns:
            dict with equity_paths, statistics, risk metrics
        """
        # Validation
        win_rate = np.clip(win_rate, 0.01, 0.99)
        avg_rr = max(avg_rr, 0.1)
        risk_per_trade = np.clip(risk_per_trade, 0.001, 0.10)  # Max 10% per trade
        
        # Generate random outcomes for all simulations
        # Shape: (num_simulations, num_trades)
        random_outcomes = np.random.random((num_simulations, num_trades))
        
        # Determine wins (1) and losses (-1)
        # Vectorized: win if random < win_rate
        outcomes = np.where(random_outcomes < win_rate, 1, -1)
        
        # Calculate returns for each trade
        # Win: +risk_per_trade * avg_rr
        # Loss: -risk_per_trade
        returns = np.where(
            outcomes == 1,
            risk_per_trade * avg_rr,
            -risk_per_trade
        )
        
        # Calculate equity paths using cumulative product
        # equity[i] = starting_capital * (1 + return[0]) * (1 + return[1]) * ...
        equity_multipliers = 1 + returns
        
        # Cumulative product along trades axis
        cumulative_multipliers = np.cumprod(equity_multipliers, axis=1)
        
        # Add starting point (all start at 1.0)
        cumulative_with_start = np.column_stack([
            np.ones(num_simulations),
            cumulative_multipliers
        ])
        
        # Convert to equity values
        equity_paths = starting_capital * cumulative_with_start
        
        # Calculate final equity for each simulation
        final_equity = equity_paths[:, -1]
        
        # Statistics
        expected_equity = np.mean(final_equity)
        median_equity = np.median(final_equity)
        percentile_5 = np.percentile(final_equity, 5)
        percentile_95 = np.percentile(final_equity, 95)
        
        # Risk of Ruin: % of paths that go below 50% of starting capital
        ruin_threshold = starting_capital * 0.5
        paths_ruined = np.any(equity_paths < ruin_threshold, axis=1)
        risk_of_ruin = np.mean(paths_ruined)
        
        # Maximum drawdown for each path
        max_drawdowns = self._calculate_drawdowns(equity_paths)
        avg_max_drawdown = np.mean(max_drawdowns)
        worst_drawdown = np.max(max_drawdowns)
        
        # Probability of profit
        prob_profit = np.mean(final_equity > starting_capital)
        
        # Average return
        avg_return_pct = ((expected_equity / starting_capital) - 1) * 100
        
        # Store for later retrieval
        self.last_simulation = {
            'equity_paths': equity_paths,
            'params': {
                'win_rate': win_rate,
                'avg_rr': avg_rr,
                'risk_per_trade': risk_per_trade,
                'num_simulations': num_simulations,
                'num_trades': num_trades,
                'starting_capital': starting_capital
            }
        }
        
        return {
            'expected_equity': round(expected_equity, 2),
            'median_equity': round(median_equity, 2),
            'percentile_5_equity': round(percentile_5, 2),
            'percentile_95_equity': round(percentile_95, 2),
            'risk_of_ruin': round(risk_of_ruin, 4),
            'avg_max_drawdown_pct': round(avg_max_drawdown, 2),
            'worst_drawdown_pct': round(worst_drawdown, 2),
            'probability_of_profit': round(prob_profit, 3),
            'avg_return_pct': round(avg_return_pct, 2),
            'equity_paths': equity_paths,
            'starting_capital': starting_capital,
            'num_simulations': num_simulations,
            'num_trades': num_trades
        }
    
    def _calculate_drawdowns(self, equity_paths: np.ndarray) -> np.ndarray:
        """
        Calculate maximum drawdown for each equity path.
        
        Args:
            equity_paths: Array of shape (num_simulations, num_trades+1)
            
        Returns:
            Array of max drawdowns (%) for each path
        """
        # Running maximum
        running_max = np.maximum.accumulate(equity_paths, axis=1)
        
        # Drawdown at each point
        drawdowns = (equity_paths - running_max) / running_max * 100
        
        # Maximum drawdown for each simulation
        max_drawdowns = np.min(drawdowns, axis=1)
        
        return max_drawdowns
    
    def analyze_strategy_risk(
        self,
        strategy: Dict[str, Any],
        account_size: float = 100000.0,
        position_size: float = 10000.0
    ) -> Dict[str, Any]:
        """
        Analyze risk for a specific options strategy.
        
        Args:
            strategy: Strategy dict with max_profit, max_loss
            account_size: Total account equity
            position_size: Capital allocated to this trade
            
        Returns:
            dict with risk metrics
        """
        max_profit = strategy.get('max_profit', 0)
        max_loss = abs(strategy.get('max_loss', 0))
        
        if max_loss == 0:
            return {
                'error': 'Max loss is zero',
                'capital_at_risk_pct': 0,
                'risk_acceptable': False
            }
        
        # Capital at risk
        capital_at_risk = min(max_loss, position_size)
        capital_at_risk_pct = (capital_at_risk / account_size) * 100
        
        # Risk-reward
        rr_ratio = max_profit / max_loss if max_loss > 0 else 0
        
        # Position size as % of account
        position_pct = (position_size / account_size) * 100
        
        # Risk assessment
        risk_acceptable = True
        warnings = []
        
        if capital_at_risk_pct > 5.0:
            risk_acceptable = False
            warnings.append(f"⚠️ Risk too high: {capital_at_risk_pct:.1f}% of account")
        
        if position_pct > 20.0:
            warnings.append(f"⚠️ Large position: {position_pct:.1f}% of account")
        
        if rr_ratio < 1.0:
            warnings.append(f"⚠️ Poor risk-reward: {rr_ratio:.2f}")
        
        return {
            'capital_at_risk': round(capital_at_risk, 2),
            'capital_at_risk_pct': round(capital_at_risk_pct, 2),
            'position_size': position_size,
            'position_pct': round(position_pct, 2),
            'risk_reward_ratio': round(rr_ratio, 2),
            'risk_acceptable': risk_acceptable,
            'warnings': warnings,
            'max_consecutive_losses_sustainable': int(account_size / capital_at_risk) if capital_at_risk > 0 else 999
        }
    
    def calculate_required_win_rate(
        self,
        avg_rr: float,
        target_return: float = 0.20  # 20% return
    ) -> Dict[str, float]:
        """
        Calculate minimum win rate needed for profitability.
        
        Breakeven: win_rate = 1 / (1 + avg_rr)
        
        Args:
            avg_rr: Average risk-reward ratio
            target_return: Desired return (e.g., 0.20 = 20%)
            
        Returns:
            dict with breakeven and target win rates
        """
        # Breakeven win rate
        breakeven_wr = 1 / (1 + avg_rr) if avg_rr > 0 else 0.5
        
        # For target return, solve: win_rate * rr - (1 - win_rate) = target_return
        # Simplified: win_rate = (target_return + 1) / (rr + 1)
        target_wr = (target_return + 1) / (avg_rr + 1) if avg_rr > 0 else 0.5
        
        return {
            'breakeven_win_rate': round(breakeven_wr, 3),
            'target_win_rate': round(target_wr, 3),
            'interpretation': f"Need {target_wr*100:.1f}% win rate for {target_return*100:.0f}% return"
        }
    
    def stress_test(
        self,
        base_win_rate: float,
        avg_rr: float,
        stress_scenarios: Optional[Dict[str, float]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Stress test across different win rate scenarios.
        
        Args:
            base_win_rate: Base case win rate
            avg_rr: Risk-reward ratio
            stress_scenarios: Optional dict of scenario_name: win_rate_adjustment
            
        Returns:
            dict of scenarios with simulation results
        """
        if stress_scenarios is None:
            stress_scenarios = {
                'base_case': 0.0,
                'pessimistic': -0.10,  # -10% win rate
                'optimistic': +0.10,   # +10% win rate
                'worst_case': -0.20    # -20% win rate
            }
        
        results = {}
        
        for scenario_name, adjustment in stress_scenarios.items():
            adjusted_wr = np.clip(base_win_rate + adjustment, 0.05, 0.95)
            
            # Run quick simulation (fewer paths for speed)
            sim_result = self.simulate_equity_paths(
                win_rate=adjusted_wr,
                avg_rr=avg_rr,
                risk_per_trade=0.02,
                num_simulations=500,
                num_trades=100,
                starting_capital=100000.0
            )
            
            results[scenario_name] = {
                'win_rate': adjusted_wr,
                'expected_equity': sim_result['expected_equity'],
                'risk_of_ruin': sim_result['risk_of_ruin'],
                'avg_return_pct': sim_result['avg_return_pct']
            }
        
        return results
    
    def get_equity_percentiles(
        self,
        equity_paths: Optional[np.ndarray] = None,
        percentiles: Optional[list] = None
    ) -> pd.DataFrame:
        """
        Extract percentile bands for visualization.
        
        Args:
            equity_paths: Optional paths array (uses last simulation if None)
            percentiles: List of percentiles to extract (default: [5, 25, 50, 75, 95])
            
        Returns:
            DataFrame with percentile bands over time
        """
        if equity_paths is None:
            if self.last_simulation is None:
                raise ValueError("No simulation run yet")
            equity_paths = self.last_simulation['equity_paths']
        
        if percentiles is None:
            percentiles = [5, 25, 50, 75, 95]
        
        num_trades = equity_paths.shape[1]
        
        # Calculate percentiles at each time step
        percentile_data = {}
        for p in percentiles:
            percentile_data[f'p{p}'] = np.percentile(equity_paths, p, axis=0)
        
        df = pd.DataFrame(percentile_data)
        df['trade'] = range(num_trades)
        
        return df


def quick_risk_assessment(
    win_rate: float,
    avg_rr: float,
    risk_per_trade: float = 0.02
) -> Dict[str, Any]:
    """
    Quick risk assessment without full simulation.
    
    Args:
        win_rate: Win rate (0-1)
        avg_rr: Risk-reward ratio
        risk_per_trade: Risk per trade as fraction
        
    Returns:
        dict with expected value and kelly fraction
    """
    # Expected value per trade
    ev_per_trade = (win_rate * avg_rr) - (1 - win_rate)
    
    # Kelly fraction
    kelly = (win_rate * avg_rr - (1 - win_rate)) / avg_rr if avg_rr > 0 else 0
    kelly = max(0, kelly)  # Can't be negative
    
    # Recommendation
    if ev_per_trade > 0.30:
        recommendation = "Excellent edge"
    elif ev_per_trade > 0.15:
        recommendation = "Good edge"
    elif ev_per_trade > 0:
        recommendation = "Slight edge"
    else:
        recommendation = "Negative expectancy - DO NOT TRADE"
    
    # Safety check
    safe_risk = min(risk_per_trade, kelly * 0.25) if kelly > 0 else 0.01
    
    return {
        'ev_per_trade': round(ev_per_trade, 3),
        'kelly_fraction': round(kelly, 3),
        'recommended_risk': round(safe_risk, 4),
        'recommendation': recommendation,
        'is_profitable': ev_per_trade > 0
    }


# Statistical utilities

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.065) -> float:
    """
    Calculate Sharpe ratio from returns.
    
    Args:
        returns: Array of returns
        risk_free_rate: Annual risk-free rate (India ~6.5%)
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free
    sharpe = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)
    
    return sharpe


def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.065) -> float:
    """
    Calculate Sortino ratio (only downside deviation).
    
    Args:
        returns: Array of returns
        risk_free_rate: Annual risk-free rate
        
    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / 252)
    downside_returns = returns[returns < 0]
    
    if len(downside_returns) == 0 or np.std(downside_returns) == 0:
        return 0.0
    
    sortino = np.mean(excess_returns) / np.std(downside_returns) * np.sqrt(252)
    
    return sortino

"""
Greeks Calculator for Options

Implements Black-Scholes Greeks computation:
- Delta: Rate of change of option price with respect to underlying
- Gamma: Rate of change of delta
- Theta: Time decay
- Vega: Sensitivity to volatility changes
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Tuple
from datetime import datetime


class GreeksCalculator:
    """
    Calculate option Greeks using Black-Scholes model.
    """
    
    def __init__(self, risk_free_rate: float = 0.065):
        """
        Initialize Greeks calculator.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 6.5% for India)
        """
        self.risk_free_rate = risk_free_rate
        
    def calculate_greeks(self,
                        spot: float,
                        strike: float,
                        time_to_expiry: float,
                        volatility: float,
                        option_type: str = 'CE') -> Dict[str, float]:
        """
        Calculate all Greeks for an option.
        
        Args:
            spot: Current underlying price
            strike: Strike price
            time_to_expiry: Time to expiry in years
            volatility: Implied volatility (as decimal, e.g., 0.20 for 20%)
            option_type: 'CE' for call, 'PE' for put
            
        Returns:
            Dictionary with Delta, Gamma, Theta, Vega, Rho
        """
        # Handle edge cases
        if time_to_expiry <= 0:
            return self._expiry_greeks(spot, strike, option_type)
        
        if volatility <= 0:
            volatility = 0.01  # Minimum volatility
            
        # Black-Scholes parameters
        d1 = self._calculate_d1(spot, strike, time_to_expiry, volatility)
        d2 = d1 - volatility * np.sqrt(time_to_expiry)
        
        # Calculate Greeks
        delta = self._calculate_delta(d1, d2, option_type)
        gamma = self._calculate_gamma(spot, d1, time_to_expiry, volatility)
        theta = self._calculate_theta(spot, strike, d1, d2, time_to_expiry, volatility, option_type)
        vega = self._calculate_vega(spot, d1, time_to_expiry)
        rho = self._calculate_rho(strike, d2, time_to_expiry, option_type)
        
        return {
            'Delta': delta,
            'Gamma': gamma,
            'Theta': theta,
            'Vega': vega,
            'Rho': rho
        }
        
    def _calculate_d1(self, S: float, K: float, T: float, sigma: float) -> float:
        """Calculate d1 parameter."""
        return (np.log(S / K) + (self.risk_free_rate + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        
    def _calculate_delta(self, d1: float, d2: float, option_type: str) -> float:
        """Calculate Delta."""
        if option_type == 'CE':
            return norm.cdf(d1)
        else:  # PE
            return norm.cdf(d1) - 1
            
    def _calculate_gamma(self, S: float, d1: float, T: float, sigma: float) -> float:
        """Calculate Gamma."""
        return norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
    def _calculate_theta(self, S: float, K: float, d1: float, d2: float, 
                        T: float, sigma: float, option_type: str) -> float:
        """Calculate Theta (per day)."""
        term1 = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        
        if option_type == 'CE':
            term2 = -self.risk_free_rate * K * np.exp(-self.risk_free_rate * T) * norm.cdf(d2)
        else:  # PE
            term2 = self.risk_free_rate * K * np.exp(-self.risk_free_rate * T) * norm.cdf(-d2)
            
        # Return theta per day (divide by 365)
        return (term1 + term2) / 365
        
    def _calculate_vega(self, S: float, d1: float, T: float) -> float:
        """Calculate Vega (per 1% change in volatility)."""
        return S * norm.pdf(d1) * np.sqrt(T) / 100
        
    def _calculate_rho(self, K: float, d2: float, T: float, option_type: str) -> float:
        """Calculate Rho (per 1% change in interest rate)."""
        if option_type == 'CE':
            return K * T * np.exp(-self.risk_free_rate * T) * norm.cdf(d2) / 100
        else:  # PE
            return -K * T * np.exp(-self.risk_free_rate * T) * norm.cdf(-d2) / 100
            
    def _expiry_greeks(self, spot: float, strike: float, option_type: str) -> Dict[str, float]:
        """Greeks at expiry (time = 0)."""
        if option_type == 'CE':
            delta = 1.0 if spot > strike else 0.0
        else:
            delta = -1.0 if spot < strike else 0.0
            
        return {
            'Delta': delta,
            'Gamma': 0.0,
            'Theta': 0.0,
            'Vega': 0.0,
            'Rho': 0.0
        }
        
    def calculate_portfolio_greeks(self, positions: list) -> Dict[str, float]:
        """
        Calculate aggregate Greeks for a portfolio of options.
        
        Args:
            positions: List of dicts with keys: spot, strike, time_to_expiry, 
                      volatility, option_type, quantity, position (buy/sell)
                      
        Returns:
            Dictionary with aggregated Greeks
        """
        total_greeks = {
            'Delta': 0.0,
            'Gamma': 0.0,
            'Theta': 0.0,
            'Vega': 0.0,
            'Rho': 0.0
        }
        
        for pos in positions:
            greeks = self.calculate_greeks(
                pos['spot'],
                pos['strike'],
                pos['time_to_expiry'],
                pos['volatility'],
                pos['option_type']
            )
            
            # Determine multiplier (positive for buy, negative for sell)
            multiplier = pos['quantity'] if pos['position'] == 'buy' else -pos['quantity']
            
            # Aggregate with multiplier
            for greek_name, greek_value in greeks.items():
                total_greeks[greek_name] += greek_value * multiplier
                
        return total_greeks


if __name__ == "__main__":
    # Test Greeks calculator
    calc = GreeksCalculator()
    
    # Example: Calculate Greeks for ATM call
    greeks = calc.calculate_greeks(
        spot=25000,
        strike=25000,
        time_to_expiry=30/365,  # 30 days
        volatility=0.15,  # 15%
        option_type='CE'
    )
    
    print("=== Greeks for ATM Call ===")
    for name, value in greeks.items():
        print(f"{name:8}: {value:10.4f}")
    
    # Example: Portfolio Greeks
    positions = [
        {
            'spot': 25000,
            'strike': 25000,
            'time_to_expiry': 30/365,
            'volatility': 0.15,
            'option_type': 'CE',
            'quantity': 50,
            'position': 'sell'
        },
        {
            'spot': 25000,
            'strike': 25200,
            'time_to_expiry': 30/365,
            'volatility': 0.16,
            'option_type': 'CE',
            'quantity': 50,
            'position': 'buy'
        }
    ]
    
    portfolio_greeks = calc.calculate_portfolio_greeks(positions)
    
    print("\n=== Portfolio Greeks (Credit Spread) ===")
    for name, value in portfolio_greeks.items():
        print(f"{name:8}: {value:10.4f}")

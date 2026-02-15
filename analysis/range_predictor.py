"""
Next-Day Nifty Range Predictor

Predicts expected trading range for next day using:
- Historical ATR
- IV from options
- VIX levels
- PCR behavior
- OI concentration

Provides multiple prediction methods with confidence scores.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from scipy import stats


class RangePredictor:
    """
    Predicts next-day Nifty trading range using multiple methods.
    """
    
    def __init__(self, options_data: pd.DataFrame, 
                 historical_nifty: pd.DataFrame,
                 current_vix: float,
                 current_spot: float):
        """
        Initialize range predictor.
        
        Args:
            options_data: Current options chain data
            historical_nifty: Historical Nifty OHLCV data
            current_vix: Current VIX value
            current_spot: Current Nifty spot price
        """
        self.options_data = options_data
        self.historical_nifty = historical_nifty
        self.current_vix = current_vix
        self.current_spot = current_spot
        
    def predict_statistical(self, period: int = 30) -> Dict:
        """
        Statistical approach using ATR and volatility with FAT-TAIL ADJUSTMENT.
        
        ⚠️ IMPORTANT: Uses empirical distribution instead of normal assumption.
        Normal distribution underestimates tail moves by 1.5-2x in markets.
        
        Args:
            period: Historical period for ATR calculation
            
        Returns:
            Dictionary with predicted range (normal + fat-tail adjusted)
        """
        # Calculate ATR
        atr = self._calculate_atr(period)
        
        # VIX-based volatility scaling
        # VIX represents annualized volatility, convert to daily
        daily_vol_pct = (self.current_vix / 100) / np.sqrt(252)
        
        # Expected move based on spot and daily volatility
        vol_based_move = self.current_spot * daily_vol_pct
        
        # Combine ATR and volatility-based estimates
        expected_range = (atr + vol_based_move) / 2
        
        # ⚠️ FAT-TAIL ADJUSTMENT
        # Market moves often exceed normal distribution predictions
        # Use empirical distribution if we have historical returns
        fat_tail_multiplier = 1.0
        if len(self.historical_nifty) > 60:
            fat_tail_multiplier = self._calculate_fat_tail_multiplier()
        
        # Calculate confidence based on VIX consistency
        confidence = self._calculate_confidence('statistical')
        
        return {
            'method': 'statistical',
            'lower_range': self.current_spot - expected_range,
            'upper_range': self.current_spot + expected_range,
            'expected_move': expected_range,
            'fat_tail_lower': self.current_spot - expected_range * fat_tail_multiplier,
            'fat_tail_upper': self.current_spot + expected_range * fat_tail_multiplier,
            'fat_tail_multiplier': fat_tail_multiplier,
            'atr': atr,
            'vol_based_move': vol_based_move,
            'confidence': confidence,
            'note': '⚠️ fat_tail_range accounts for market tail events'
        }
    
    def predict_rule_based(self) -> Dict:
        """
        Rule-based approach using options positioning.
        
        Returns:
            Dictionary with predicted range
        """
        # Calculate PCR
        ce_oi = self.options_data[self.options_data['Option_Type'] == 'CE']['OI'].sum()
        pe_oi = self.options_data[self.options_data['Option_Type'] == 'PE']['OI'].sum()
        pcr = pe_oi / (ce_oi + 1)
        
        # Calculate OI concentration
        total_oi = self.options_data['OI'].sum()
        top_3_oi = self.options_data.nlargest(3, 'OI')['OI'].sum()
        concentration = (top_3_oi / total_oi) * 100 if total_oi > 0 else 0
        
        # Base move from ATR
        base_atr = self._calculate_atr(14)
        
        # Apply rules to adjust range
        multiplier = 1.0
        
        # Rule 1: High PCR + High VIX → Widen range
        if pcr > 1.3 and self.current_vix > 18:
            multiplier *= 1.5
            reason = "High PCR + High VIX: Expanding volatility regime"
        
        # Rule 2: Low PCR + Low VIX → Narrow range
        elif pcr < 0.7 and self.current_vix < 12:
            multiplier *= 0.7
            reason = "Low PCR + Low VIX: Compressed volatility"
        
        # Rule 3: High OI concentration far from spot → Narrow range
        elif concentration > 50:
            top_strikes = top_3_oi['Strike'].values if 'Strike' in top_3_oi.columns else []
            if top_strikes and all(abs(s - self.current_spot) > 500 for s in top_strikes):
                multiplier *= 0.8
                reason = "High OI concentration far from spot: Range-bound"
        
        # Rule 4: Low concentration → Normal to wider range
        elif concentration < 30:
            multiplier *= 1.2
            reason = "Low OI concentration: Lack of conviction"
        
        else:
            reason = "Normal market conditions"
        
        # Calculate expected range
        expected_move = base_atr * multiplier
        
        confidence = self._calculate_confidence('rule_based')
        
        return {
            'method': 'rule_based',
            'lower_range': self.current_spot - expected_move,
            'upper_range': self.current_spot + expected_move,
            'expected_move': expected_move,
            'multiplier': multiplier,
            'pcr': pcr,
            'vix': self.current_vix,
            'concentration': concentration,
            'reason': reason,
            'confidence': confidence
        }
    
    def predict_iv_based(self) -> Dict:
        """
        IV-based prediction using ATM options.
        
        Returns:
            Dictionary with predicted range
        """
        # Find ATM options
        atm_threshold = self.current_spot * 0.02  # Within 2% of spot
        
        atm_options = self.options_data[
            abs(self.options_data['Strike'] - self.current_spot) < atm_threshold
        ]
        
        if atm_options.empty:
            # Fallback to statistical method
            return self.predict_statistical()
        
        # Get ATM IV
        atm_iv = atm_options['IV'].mean()
        
        # Convert annualized IV to daily expected move
        daily_std_dev = (atm_iv / 100) / np.sqrt(252)
        expected_move = self.current_spot * daily_std_dev
        
        # One standard deviation move
        confidence = 68  # 68% probability for 1 std dev
        
        return {
            'method': 'iv_based',
            'lower_range': self.current_spot - expected_move,
            'upper_range': self.current_spot + expected_move,
            'expected_move': expected_move,
            'atm_iv': atm_iv,
            'confidence': confidence
        }
    
    def predict_ensemble(self) -> Dict:
        """
        Ensemble prediction combining all methods.
        
        Returns:
            Dictionary with consensus predicted range
        """
        # Get predictions from all methods
        statistical = self.predict_statistical()
        rule_based = self.predict_rule_based()
        iv_based = self.predict_iv_based()
        
        # Weight the predictions by confidence
        methods = [statistical, rule_based, iv_based]
        total_confidence = sum(m['confidence'] for m in methods)
        
        # Weighted average
        weighted_lower = sum(m['lower_range'] * m['confidence'] for m in methods) / total_confidence
        weighted_upper = sum(m['upper_range'] * m['confidence'] for m in methods) / total_confidence
        
        expected_move = (weighted_upper - weighted_lower) / 2
        
        # Consensus confidence
        consensus_confidence = np.mean([m['confidence'] for m in methods])
        
        return {
            'method': 'ensemble',
            'lower_range': weighted_lower,
            'upper_range': weighted_upper,
            'expected_move': expected_move,
            'expected_down_move': self.current_spot - weighted_lower,
            'expected_up_move': weighted_upper - self.current_spot,
            'confidence': consensus_confidence,
            'sub_predictions': {
                'statistical': statistical,
                'rule_based': rule_based,
                'iv_based': iv_based
            }
        }
    
    def predict_intraday_levels(self) -> Dict:
        """
        Predict intraday support and resistance levels.
        
        Returns:
            Dictionary with key levels
        """
        ensemble = self.predict_ensemble()
        
        # Calculate multiple levels
        upper_range = ensemble['upper_range']
        lower_range = ensemble['lower_range']
        
        # Fibonacci-style levels
        range_size = upper_range - lower_range
        
        levels = {
            'spot': self.current_spot,
            'upper_target': upper_range,
            'lower_target': lower_range,
            'resistance_1': self.current_spot + (range_size * 0.382),
            'resistance_2': self.current_spot + (range_size * 0.618),
            'support_1': self.current_spot - (range_size * 0.382),
            'support_2': self.current_spot - (range_size * 0.618),
            'pivot': (upper_range + lower_range) / 2
        }
        
        return levels
    
    def _calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range from historical data."""
        if len(self.historical_nifty) < period:
            return 200.0  # Default fallback
        
        df = self.historical_nifty.tail(period + 5).copy()
        
        # Calculate True Range
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = abs(df['high'] - df['close'].shift(1))
        df['low_close'] = abs(df['low'] - df['close'].shift(1))
        
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        
        # Calculate ATR
        atr = df['true_range'].tail(period).mean()
        
        return atr
    
    def _calculate_fat_tail_multiplier(self) -> float:
        """
        Calculate multiplier for fat-tail distribution.
        
        Compares empirical percentiles to normal distribution percentiles.
        Markets have heavier tails than normal distribution (fatter tails).
        
        Returns:
            Multiplier to apply to normal-distribution range (typically 1.1-1.5)
        """
        if len(self.historical_nifty) < 60:
            return 1.2  # Conservative default
        
        # Calculate daily returns
        returns = self.historical_nifty['close'].pct_change().dropna()
        
        # Calculate empirical 99th percentile (one-tailed)
        empirical_99 = np.abs(returns).quantile(0.99)
        
        # Calculate what normal distribution would predict
        # For normal: 99th percentile ≈ 2.33 standard deviations
        returns_std = returns.std()
        normal_99 = 2.33 * returns_std
        
        # Ratio gives us fat-tail multiplier
        if normal_99 > 0:
            multiplier = empirical_99 / normal_99
        else:
            multiplier = 1.0
        
        # Clamp to reasonable range
        multiplier = np.clip(multiplier, 1.0, 2.0)
        
        return multiplier
    
    def _calculate_confidence(self, method: str) -> float:
        """
        Calculate confidence score for a prediction method.
        
        Args:
            method: Prediction method name
            
        Returns:
            Confidence score (0-100)
        """
        base_confidence = 70
        
        if method == 'statistical':
            # Higher confidence with more historical data
            if len(self.historical_nifty) >= 30:
                return 75
            return 65
        
        elif method == 'rule_based':
            # Confidence based on OI and volume
            total_oi = self.options_data['OI'].sum()
            total_volume = self.options_data['Volume'].sum()
            
            if total_oi > 1000000 and total_volume > 100000:
                return 80
            return 70
        
        elif method == 'iv_based':
            # Confidence based on IV availability and spread
            atm_threshold = self.current_spot * 0.02
            atm_options = self.options_data[
                abs(self.options_data['Strike'] - self.current_spot) < atm_threshold
            ]
            
            if not atm_options.empty and atm_options['IV'].std() < 5:
                return 75
            return 65
        
        return base_confidence
    
    def get_prediction_report(self) -> str:
        """
        Generate formatted prediction report.
        
        Returns:
            Formatted string with predictions
        """
        ensemble = self.predict_ensemble()
        levels = self.predict_intraday_levels()
        
        report = []
        report.append("\n" + "="*60)
        report.append("NEXT-DAY RANGE PREDICTION")
        report.append("="*60)
        report.append(f"Current Spot: {self.current_spot:,.2f}")
        report.append(f"Current VIX: {self.current_vix:.2f}")
        report.append("")
        
        report.append("ENSEMBLE PREDICTION:")
        report.append(f"  Expected Range: {ensemble['lower_range']:,.2f} - {ensemble['upper_range']:,.2f}")
        report.append(f"  Expected Up-Move: +{ensemble['expected_up_move']:.2f} points")
        report.append(f"  Expected Down-Move: -{ensemble['expected_down_move']:.2f} points")
        report.append(f"  Confidence: {ensemble['confidence']:.1f}%")
        report.append("")
        
        report.append("INTRADAY LEVELS:")
        report.append(f"  Upper Target: {levels['upper_target']:,.2f}")
        report.append(f"  Resistance 1: {levels['resistance_1']:,.2f}")
        report.append(f"  Resistance 2: {levels['resistance_2']:,.2f}")
        report.append(f"  Pivot: {levels['pivot']:,.2f}")
        report.append(f"  Support 1: {levels['support_1']:,.2f}")
        report.append(f"  Support 2: {levels['support_2']:,.2f}")
        report.append(f"  Lower Target: {levels['lower_target']:,.2f}")
        report.append("")
        
        report.append("INDIVIDUAL METHODS:")
        for method_name in ['statistical', 'rule_based', 'iv_based']:
            pred = ensemble['sub_predictions'][method_name]
            report.append(f"  {method_name.upper()}:")
            report.append(f"    Range: {pred['lower_range']:,.2f} - {pred['upper_range']:,.2f}")
            report.append(f"    Confidence: {pred['confidence']:.1f}%")
        
        report.append("="*60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test range predictor with sample data
    from utils.io_helpers import OptionsDataLoader
    from api_clients.market_data import MarketDataClient
    
    loader = OptionsDataLoader("data/raw/monthly")
    weekly_data = loader.load_all_weeks()
    
    if weekly_data:
        latest_week = loader.get_latest_week()
        options_df = loader.get_data_for_week(latest_week)
        
        # Get market data
        client = MarketDataClient()
        nifty_hist = client.get_historical_nifty(days=30)
        vix_data = client.fetch_vix()
        nifty_data = client.fetch_nifty()
        
        current_vix = vix_data.get('vix_value', 15.0)
        current_spot = options_df['Spot_Price'].iloc[0] if not options_df.empty else 26000.0
        
        # Create predictor
        predictor = RangePredictor(
            options_data=options_df,
            historical_nifty=nifty_hist,
            current_vix=current_vix,
            current_spot=current_spot
        )
        
        # Generate predictions
        print(predictor.get_prediction_report())

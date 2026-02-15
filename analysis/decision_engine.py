"""
Decision Engine - Institutional-grade trading decision logic
Analyzes volatility edge, expected value, and trade quality
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class DecisionEngine:
    """
    Converts analytics into structured trading decisions.
    
    Key Functions:
    - Volatility edge detection (IV vs realized)
    - Expected value modeling
    - Trade quality scoring (0-100)
    - Directional signal integration
    - Structured decision output
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Decision Engine
        
        Args:
            config: Optional configuration dict with thresholds
        """
        self.config = config or {}
        
        # Default thresholds
        self.vol_edge_threshold = self.config.get('vol_edge_threshold', 0.15)
        self.min_trade_score = self.config.get('min_trade_score', 60)
        self.min_risk_reward = self.config.get('min_risk_reward', 1.5)
        self.max_risk_of_ruin = self.config.get('max_risk_of_ruin', 0.20)  # 20% max

        
    def compute_vol_edge(
        self, 
        option_df: pd.DataFrame, 
        historical_df: Optional[pd.DataFrame] = None,
        spot_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Detect IV vs realized volatility edge.
        
        Positive edge = IV > Historical Vol (sell premium)
        Negative edge = IV < Historical Vol (buy premium)
        
        Args:
            option_df: DataFrame with Strike, IV_CE, IV_PE columns (or IV with Option_Type)
            historical_df: Optional DataFrame with OHLC data
            spot_price: Current spot price
            
        Returns:
            dict with vol_edge_score, interpretation, metrics
        """
        try:
            # Extract ATM implied volatility
            if spot_price is None:
                spot_price = option_df['Spot_Price'].iloc[0] if 'Spot_Price' in option_df.columns else None
            
            if spot_price is None:
                return {
                    'vol_edge_score': 0.0,
                    'interpretation': 'No Spot Price Available',
                    'error': 'Cannot compute vol edge without spot price'
                }
            
            # Find ATM strike and extract IVs
            option_df_sorted = option_df.copy()
            option_df_sorted['distance_to_atm'] = abs(option_df_sorted['Strike'] - spot_price)
            
            iv_ce = 0.0
            iv_pe = 0.0
            
            # Method 1: Pivoted format (IV_CE and IV_PE columns)
            if 'IV_CE' in option_df.columns and 'IV_PE' in option_df.columns:
                atm_row = option_df_sorted.loc[option_df_sorted['distance_to_atm'].idxmin()]
                iv_ce = atm_row.get('IV_CE', 0)
                iv_pe = atm_row.get('IV_PE', 0)
            
            # Method 2: Row-by-row format (Option_Type column with separate rows)
            elif 'Option_Type' in option_df.columns and 'IV' in option_df.columns:
                # Separate CE and PE rows
                atm_ce = option_df_sorted[option_df_sorted['Option_Type'] == 'CE']
                atm_pe = option_df_sorted[option_df_sorted['Option_Type'] == 'PE']
                
                if not atm_ce.empty:
                    iv_ce = atm_ce.loc[atm_ce['distance_to_atm'].idxmin(), 'IV']
                
                if not atm_pe.empty:
                    iv_pe = atm_pe.loc[atm_pe['distance_to_atm'].idxmin(), 'IV']
            
            # Method 3: Alternate column names
            elif 'IV_Call' in option_df.columns or 'IV_Put' in option_df.columns:
                atm_row = option_df_sorted.loc[option_df_sorted['distance_to_atm'].idxmin()]
                iv_ce = atm_row.get('IV_Call', 0)
                iv_pe = atm_row.get('IV_Put', 0)
            
            # Calculate average IV
            atm_iv = 0.0
            if iv_ce and iv_pe:
                atm_iv = (float(iv_ce) + float(iv_pe)) / 2.0
            elif iv_ce:
                atm_iv = float(iv_ce)
            elif iv_pe:
                atm_iv = float(iv_pe)
            
            if atm_iv == 0:
                return {
                    'vol_edge_score': 0.0,
                    'interpretation': 'No IV Data Available - Using Default Analysis',
                    'atm_iv': 0.0,
                    'warning': 'IV columns not found; check data format'
                }
            
            # Calculate realized volatility if historical data provided
            realized_vol = None
            if historical_df is not None and len(historical_df) > 5:
                # 30-day realized volatility
                returns = historical_df['Close'].pct_change().dropna()
                realized_vol = returns.std() * np.sqrt(252)  # Annualized
            else:
                # Use typical NIFTY realized vol estimate (15-20%)
                realized_vol = 0.18
            
            # Compute volatility edge
            vol_edge = (atm_iv - realized_vol) / realized_vol
            
            # Normalize to -1 to +1 scale
            vol_edge_score = np.clip(vol_edge, -1.0, 1.0)
            
            # Interpretation
            if vol_edge_score > 0.20:
                interpretation = "Strong Premium Selling Edge"
            elif vol_edge_score > 0.10:
                interpretation = "Moderate Premium Selling Edge"
            elif vol_edge_score > -0.10:
                interpretation = "Neutral Volatility"
            elif vol_edge_score > -0.20:
                interpretation = "Moderate Long Vol Edge"
            else:
                interpretation = "Strong Long Vol Edge"
            
            return {
                'vol_edge_score': round(vol_edge_score, 3),
                'interpretation': interpretation,
                'atm_iv': round(atm_iv, 4),
                'realized_vol': round(realized_vol, 4),
                'atm_strike': float(atm_row['Strike']),
                'raw_edge': round(vol_edge, 3)
            }
            
        except Exception as e:
            return {
                'vol_edge_score': 0.0,
                'interpretation': 'Error Computing Vol Edge',
                'error': str(e)
            }
    
    def compute_expected_value(
        self,
        strategy: Dict[str, Any],
        range_probs: Optional[Dict[str, float]] = None,
        spot_price: float = 23000.0,
        days_to_expiry: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate expected value of strategy using probabilistic payoff.
        
        Args:
            strategy: Dict with legs, max_profit, max_loss, breakevens
            range_probs: Optional probability distribution from range predictor
            spot_price: Current NIFTY spot
            days_to_expiry: DTE for simulation
            
        Returns:
            dict with expected_value, positive_probability, risk_reward_ratio
        """
        try:
            max_profit = strategy.get('max_profit', 0)
            max_loss = abs(strategy.get('max_loss', 0))
            breakevens = strategy.get('breakevens', [])
            
            if max_loss == 0:
                return {
                    'expected_value': 0.0,
                    'positive_probability': 0.5,
                    'risk_reward_ratio': 0.0,
                    'error': 'Max loss is zero'
                }
            
            # If no range probs provided, use normal distribution assumption
            if range_probs is None:
                # Assume 1 stdev move = 5% of spot
                std_move = spot_price * 0.05 * np.sqrt(days_to_expiry / 30)
                
                # Approximate win probability based on breakevens
                if len(breakevens) == 2:
                    # Range strategy (e.g., Iron Condor)
                    lower_be = min(breakevens)
                    upper_be = max(breakevens)
                    
                    # Prob in range using normal CDF
                    from scipy.stats import norm
                    z_lower = (lower_be - spot_price) / std_move
                    z_upper = (upper_be - spot_price) / std_move
                    
                    win_prob = norm.cdf(z_upper) - norm.cdf(z_lower)
                    
                elif len(breakevens) == 1:
                    # Directional strategy
                    be = breakevens[0]
                    
                    # Determine if bullish or bearish
                    if be > spot_price:
                        # Bullish - need spot above BE
                        from scipy.stats import norm
                        z = (be - spot_price) / std_move
                        win_prob = 1 - norm.cdf(z)
                    else:
                        # Bearish - need spot below BE
                        from scipy.stats import norm
                        z = (be - spot_price) / std_move
                        win_prob = norm.cdf(z)
                else:
                    # Unknown structure, assume 50/50
                    win_prob = 0.5
            else:
                # Use provided probabilities
                win_prob = range_probs.get('win_probability', 0.5)
            
            # Clamp probability
            win_prob = np.clip(win_prob, 0.01, 0.99)
            
            # Expected Value
            ev = (win_prob * max_profit) - ((1 - win_prob) * max_loss)
            
            # Risk-reward ratio
            rr_ratio = max_profit / max_loss if max_loss > 0 else 0
            
            return {
                'expected_value': round(ev, 2),
                'positive_probability': round(win_prob, 3),
                'risk_reward_ratio': round(rr_ratio, 2),
                'max_profit': max_profit,
                'max_loss': -max_loss,
                'interpretation': 'Positive EV' if ev > 0 else 'Negative EV'
            }
            
        except Exception as e:
            return {
                'expected_value': 0.0,
                'positive_probability': 0.5,
                'risk_reward_ratio': 0.0,
                'error': str(e)
            }
    
    def compute_trade_score(
        self,
        vol_edge: Dict[str, Any],
        ev_metrics: Dict[str, Any],
        market_metrics: Dict[str, Any],
        liquidity_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        Compute overall trade quality score (0-100).
        
        Formula:
        TradeScore = 0.25 * vol_alignment + 0.25 * vol_edge 
                   + 0.20 * risk_reward + 0.15 * oi_support 
                   + 0.15 * liquidity
        
        Args:
            vol_edge: Output from compute_vol_edge()
            ev_metrics: Output from compute_expected_value()
            market_metrics: Dict with PCR, max_pain, trend indicators
            liquidity_metrics: Optional liquidity analysis
            
        Returns:
            dict with trade_score (0-100) and confidence_level
        """
        try:
            score_components = []
            
            # 1. Volatility Edge Component (25%)
            vol_edge_score = vol_edge.get('vol_edge_score', 0)
            vol_component = (abs(vol_edge_score) * 100) * 0.25
            score_components.append(vol_component)
            
            # 2. Regime Alignment (25%) - based on PCR and trends
            pcr = market_metrics.get('pcr', 1.0)
            
            # PCR scoring: 0.7-1.3 is neutral, extremes are better
            if pcr < 0.7:
                regime_score = 80  # Bullish extreme
            elif pcr > 1.3:
                regime_score = 80  # Bearish extreme
            elif 0.8 <= pcr <= 1.2:
                regime_score = 50  # Neutral
            else:
                regime_score = 65  # Mild directional
            
            regime_component = regime_score * 0.25
            score_components.append(regime_component)
            
            # 3. Risk-Reward Component (20%)
            rr_ratio = ev_metrics.get('risk_reward_ratio', 0)
            
            # Score RR: 2.0+ is excellent, 1.5+ is good
            if rr_ratio >= 2.0:
                rr_score = 100
            elif rr_ratio >= 1.5:
                rr_score = 80
            elif rr_ratio >= 1.0:
                rr_score = 60
            else:
                rr_score = 40
            
            rr_component = rr_score * 0.20
            score_components.append(rr_component)
            
            # 4. OI Support Component (15%)
            total_oi = market_metrics.get('total_oi', 0)
            
            # Higher OI = better liquidity and market participation
            if total_oi > 5_000_000:
                oi_score = 90
            elif total_oi > 2_000_000:
                oi_score = 70
            elif total_oi > 1_000_000:
                oi_score = 50
            else:
                oi_score = 30
            
            oi_component = oi_score * 0.15
            score_components.append(oi_component)
            
            # 5. Liquidity Component (15%)
            if liquidity_metrics:
                liquidity_score = liquidity_metrics.get('score', 70)
            else:
                # Default reasonable liquidity for NIFTY
                liquidity_score = 75
            
            liquidity_component = liquidity_score * 0.15
            score_components.append(liquidity_component)
            
            # Total Score
            trade_score = int(sum(score_components))
            trade_score = np.clip(trade_score, 0, 100)
            
            # Confidence Level
            if trade_score >= 75:
                confidence = "High"
            elif trade_score >= 60:
                confidence = "Medium"
            else:
                confidence = "Low"
            
            return {
                'trade_score': trade_score,
                'confidence_level': confidence,
                'components': {
                    'vol_edge': round(vol_component, 1),
                    'regime': round(regime_component, 1),
                    'risk_reward': round(rr_component, 1),
                    'oi_support': round(oi_component, 1),
                    'liquidity': round(liquidity_component, 1)
                }
            }
            
        except Exception as e:
            return {
                'trade_score': 50,
                'confidence_level': 'Low',
                'error': str(e)
            }
    
    def generate_trade_decision(
        self,
        vol_edge: Dict[str, Any],
        ev_metrics: Dict[str, Any],
        trade_score: Dict[str, Any],
        risk_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate final structured trading decision.
        
        Args:
            vol_edge: Volatility edge analysis
            ev_metrics: Expected value metrics
            trade_score: Trade quality score
            risk_metrics: Optional risk engine output
            
        Returns:
            Structured decision with trade_allowed, confidence, reasoning
        """
        try:
            reasoning = []
            trade_allowed = True
            risk_flags = []
            
            # Check vol edge
            vol_edge_score = vol_edge.get('vol_edge_score', 0)
            if abs(vol_edge_score) > 0.15:
                reasoning.append(f"✅ {vol_edge.get('interpretation', 'Vol edge detected')}")
            else:
                reasoning.append("⚠️ Neutral volatility environment")
                risk_flags.append("Low vol edge")
            
            # Check EV
            ev = ev_metrics.get('expected_value', 0)
            if ev > 0:
                reasoning.append(f"✅ Positive expected value: ₹{ev:.0f}")
            else:
                reasoning.append(f"❌ Negative expected value: ₹{ev:.0f}")
                trade_allowed = False
                risk_flags.append("Negative EV")
            
            # Check risk-reward
            rr = ev_metrics.get('risk_reward_ratio', 0)
            if rr >= 1.5:
                reasoning.append(f"✅ Good risk-reward: {rr:.2f}")
            else:
                reasoning.append(f"⚠️ Low risk-reward: {rr:.2f}")
                risk_flags.append("Poor R:R")
            
            # Check trade score
            score = trade_score.get('trade_score', 50)
            if score >= self.min_trade_score:
                reasoning.append(f"✅ Trade score: {score}/100 ({trade_score.get('confidence_level')})")
            else:
                reasoning.append(f"❌ Trade score too low: {score}/100")
                trade_allowed = False
                risk_flags.append("Low trade score")
            
            # Risk of Ruin check
            if risk_metrics:
                ror = risk_metrics.get('risk_of_ruin', 0)
                if ror > 0.05:  # 5% threshold
                    reasoning.append(f"❌ High risk of ruin: {ror*100:.1f}%")
                    trade_allowed = False
                    risk_flags.append("High risk of ruin")
                else:
                    reasoning.append(f"✅ Acceptable risk of ruin: {ror*100:.1f}%")
            
            # Final confidence
            confidence = score
            
            # Override if critical issues
            if len(risk_flags) >= 3:
                trade_allowed = False
                reasoning.append("❌ Multiple risk factors present")
            
            return {
                'trade_allowed': trade_allowed,
                'confidence': confidence,
                'risk_flags': risk_flags,
                'reasoning': reasoning,
                'timestamp': datetime.now().isoformat(),
                'summary': self._generate_summary(trade_allowed, confidence, risk_flags)
            }
            
        except Exception as e:
            return {
                'trade_allowed': False,
                'confidence': 0,
                'risk_flags': ['Error in decision generation'],
                'reasoning': [f"Error: {str(e)}"],
                'timestamp': datetime.now().isoformat(),
                'summary': "Cannot make decision due to error"
            }
    
    def _generate_summary(
        self, 
        trade_allowed: bool, 
        confidence: int, 
        risk_flags: List[str]
    ) -> str:
        """Generate human-readable summary"""
        if not trade_allowed:
            return f"❌ DO NOT TRADE - {len(risk_flags)} risk factor(s) detected"
        elif confidence >= 75:
            return f"✅ TRADE RECOMMENDED - High confidence ({confidence}/100)"
        elif confidence >= 60:
            return f"⚠️ TRADE WITH CAUTION - Medium confidence ({confidence}/100)"
        else:
            return f"⚠️ MARGINAL TRADE - Low confidence ({confidence}/100)"
    
    def validate_with_directional_signal(
        self,
        directional_signal: Any,  # DirectionalSignal object
        strategy_type: str,  # "LONG_CALL", "LONG_PUT", "IRON_CONDOR", etc
        vol_edge_score: float,
        risk_of_ruin: float = 0.0
    ) -> Dict[str, Any]:
        """
        Validate trading decision using directional signal.
        
        YOUR TRADING STYLE:
        - Only take directional trades (LONG_CALL / LONG_PUT) when directional signal exists
        - Allow neutral strategies when signal is NO_SIGNAL
        - Reject trades if directional signal conflicts with strategy type
        
        Args:
            directional_signal: DirectionalSignal object with signal, confidence
            strategy_type: Type of strategy ("LONG_CALL", "LONG_PUT", "IRON_CONDOR", etc)
            vol_edge_score: Volatility edge (-1.0 to +1.0)
            risk_of_ruin: Estimated probability of ruin (0-1)
            
        Returns:
            dict with:
            - allowed: bool, whether to take this trade
            - confidence: 0-100 score
            - reasons: list of decision reasoning
            - warnings: list of alerts
        """
        allowed = True
        reasons = []
        warnings = []
        confidence = 50
        
        # Extract signal
        signal_type = directional_signal.signal
        signal_confidence = directional_signal.confidence
        
        # Check directional alignment
        if strategy_type == "LONG_CALL":
            if signal_type == "CALL_BUY":
                reasons.append(f"✅ Signal {signal_type} aligns with {strategy_type}")
                confidence = signal_confidence
            elif signal_type == "NO_SIGNAL":
                reasons.append(f"⚠️ No directional signal for {strategy_type}")
                allowed = False
            else:
                reasons.append(f"❌ Signal {signal_type} conflicts with {strategy_type}")
                allowed = False
        
        elif strategy_type == "LONG_PUT":
            if signal_type == "PUT_BUY":
                reasons.append(f"✅ Signal {signal_type} aligns with {strategy_type}")
                confidence = signal_confidence
            elif signal_type == "NO_SIGNAL":
                reasons.append(f"⚠️ No directional signal for {strategy_type}")
                allowed = False
            else:
                reasons.append(f"❌ Signal {signal_type} conflicts with {strategy_type}")
                allowed = False
        
        elif strategy_type in ["IRON_CONDOR", "STRANGLE", "BUTTERFLY"]:
            # Neutral strategies OK when no signal
            if signal_type == "NO_SIGNAL":
                reasons.append(f"✅ Neutral market → {strategy_type} appropriate")
                confidence = 70  # Baseline for neutral strategies
            else:
                reasons.append(f"⚠️ Directional signal {signal_type} for neutral strategy {strategy_type}")
                warnings.append("Consider taking directional trade instead")
                confidence = min(50, signal_confidence)
        
        # Check vol edge
        if vol_edge_score > 0.15:
            reasons.append(f"✅ Strong premium selling edge ({vol_edge_score:.1%})")
            confidence = min(100, confidence + 10)
        elif vol_edge_score < -0.15:
            reasons.append(f"⚠️ Premium buying edge ({vol_edge_score:.1%}), less attractive")
            confidence = max(0, confidence - 5)
        
        # Check risk of ruin
        if risk_of_ruin > self.max_risk_of_ruin:
            warnings.append(f"🚨 Risk of ruin {risk_of_ruin:.1%} exceeds max {self.max_risk_of_ruin:.1%}")
            allowed = False
        elif risk_of_ruin > 0.10:
            warnings.append(f"⚠️ Risk of ruin {risk_of_ruin:.1%} is elevated")
        
        return {
            'allowed': allowed,
            'confidence': int(confidence),
            'reasons': reasons,
            'warnings': warnings,
            'signal': signal_type,
            'signal_confidence': signal_confidence
        }


# Standalone utility functions

def analyze_regime(pcr: float, vix: Optional[float] = None) -> Dict[str, str]:
    """
    Quick regime classification based on PCR and VIX.
    
    Args:
        pcr: Put-Call Ratio
        vix: Optional VIX/India VIX
        
    Returns:
        dict with regime, bias, strategy_hint
    """
    if pcr < 0.7:
        regime = "Extreme Greed"
        bias = "Bearish Contrarian"
        hint = "Consider selling calls or bearish spreads"
    elif pcr < 0.9:
        regime = "Moderate Greed"
        bias = "Neutral to Bearish"
        hint = "Neutral strategies or short premium"
    elif pcr < 1.1:
        regime = "Balanced"
        bias = "Neutral"
        hint = "Iron Condors, Butterflies"
    elif pcr < 1.3:
        regime = "Moderate Fear"
        bias = "Neutral to Bullish"
        hint = "Bullish spreads or long calls"
    else:
        regime = "Extreme Fear"
        bias = "Bullish Contrarian"
        hint = "Consider selling puts or bullish spreads"
    
    return {
        'regime': regime,
        'bias': bias,
        'strategy_hint': hint,
        'pcr': pcr
    }

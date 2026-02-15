"""
Directional Signal Engine

Generates directional trade signals based on:
- RSI (momentum)
- PCR (market sentiment)
- Confluence logic

Your trading style:
- Call buying when RSI < 30 (oversold) + PCR < 0.7 (bullish)
- Put buying when RSI > 70 (overbought) + PCR > 1.3 (bearish)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DirectionalSignal:
    """Output from directional signal engine"""
    signal: str  # "CALL_BUY" | "PUT_BUY" | "NO_SIGNAL"
    confidence: float  # 0-100
    rsi: Optional[float]
    pcr: Optional[float]
    rsi_percentile: Optional[float]
    pcr_percentile: Optional[float]
    reasons: list  # List of reasons why signal triggered/didn't trigger


class DirectionalSignalEngine:
    """
    Generates directional trade signals aligned with your trading behavior.
    """
    
    def __init__(
        self,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        pcr_oversold: float = 0.7,  # Low PCR = bullish
        pcr_overbought: float = 1.3  # High PCR = bearish
    ):
        """
        Initialize Directional Signal Engine.
        
        Args:
            rsi_oversold: RSI threshold for oversold (call buying)
            rsi_overbought: RSI threshold for overbought (put buying)
            pcr_oversold: PCR threshold for oversold (bullish)
            pcr_overbought: PCR threshold for overbought (bearish)
        """
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.pcr_oversold = pcr_oversold
        self.pcr_overbought = pcr_overbought
    
    def compute_rsi(
        self,
        price_series: pd.Series,
        period: int = 14
    ) -> float:
        """
        Compute RSI (Relative Strength Index).
        
        Standard formula:
        RSI = 100 - (100 / (1 + RS))
        where RS = Avg Gain / Avg Loss
        
        Args:
            price_series: Series of prices (usually close prices)
            period: RSI lookback period (14 is standard)
            
        Returns:
            RSI value (0-100)
        """
        # Calculate changes
        delta = price_series.diff()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0).rolling(window=period).mean()
        losses = -delta.where(delta < 0, 0).rolling(window=period).mean()
        
        # Calculate RS
        rs = gains / losses.replace(0, 1e-10)  # Avoid division by zero
        
        # Calculate RSI
        rsi = 100 - (100 / (1 + rs))
        
        # Return latest RSI
        return rsi.iloc[-1] if len(rsi) > 0 else 50.0
    
    def compute_pcr(
        self,
        option_df: pd.DataFrame,
        by_expiry: bool = False
    ) -> float:
        """
        Compute Put-Call Ratio (OI-based).
        
        PCR = Total PE OI / Total CE OI
        
        HIGH PCR (> 1.3) = Bearish (dealers long calls, people long puts)
        LOW PCR (< 0.7) = Bullish (dealers short calls, people short puts)
        
        Args:
            option_df: DataFrame with options data
            by_expiry: If True, compute only for nearest expiry
            
        Returns:
            PCR value
        """
        if by_expiry and 'Expiry' in option_df.columns:
            nearest_expiry = option_df['Expiry'].min()
            df = option_df[option_df['Expiry'] == nearest_expiry]
        else:
            df = option_df
        
        # Sum OI by option type
        ce_oi = df[df['Option_Type'] == 'CE']['OI'].sum()
        pe_oi = df[df['Option_Type'] == 'PE']['OI'].sum()
        
        # Avoid division by zero
        if ce_oi == 0:
            return np.nan
        
        pcr = pe_oi / ce_oi
        return pcr
    
    def generate_signal(
        self,
        price_series: pd.Series,
        option_df: pd.DataFrame,
        min_confluence_strength: float = 0.6
    ) -> DirectionalSignal:
        """
        Generate directional trade signal.
        
        CALL BUY Signal:
        - RSI < 30 (oversold momentum)
        - AND PCR < 0.7 (bullish sentiment)
        - Confluence confirms bullish bias
        
        PUT BUY Signal:
        - RSI > 70 (overbought momentum)
        - AND PCR > 1.3 (bearish sentiment)
        - Confluence confirms bearish bias
        
        Args:
            price_series: Price history (1H close prices recommended)
            option_df: Current options chain data
            min_confluence_strength: Minimum confluence to signal (0-1)
            
        Returns:
            DirectionalSignal object with reasoning
        """
        reasons = []
        
        # Calculate indicators
        rsi = self.compute_rsi(price_series, period=14)
        pcr = self.compute_pcr(option_df, by_expiry=True)
        
        # Calculate percentiles for scoring
        rsi_percentile = rsi / 100.0  # Normalize 0-100 to 0-1
        pcr_percentile = self._calculate_pcr_percentile(pcr)
        
        # Initialize signal
        signal = "NO_SIGNAL"
        confidence = 0.0
        
        # CALL BUY Logic
        if rsi < self.rsi_oversold and pcr < self.pcr_oversold:
            signal = "CALL_BUY"
            
            # Confidence: distance from thresholds
            rsi_distance = (self.rsi_oversold - rsi) / self.rsi_oversold
            pcr_distance = (self.pcr_oversold - pcr) / self.pcr_oversold
            
            # Confidence is average of how far we are from thresholds
            confluence = (rsi_distance + pcr_distance) / 2
            confidence = min(100, confluence * 100 * min_confluence_strength)
            
            reasons.append(f"✅ RSI {rsi:.1f} < {self.rsi_oversold} (oversold)")
            reasons.append(f"✅ PCR {pcr:.2f} < {self.pcr_oversold} (bullish)")
            reasons.append(f"Confluence strength: {confluence:.2%}")
        
        # PUT BUY Logic
        elif rsi > self.rsi_overbought and pcr > self.pcr_overbought:
            signal = "PUT_BUY"
            
            # Confidence: distance from thresholds  
            rsi_distance = (rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            pcr_distance = (pcr - self.pcr_overbought) / (2 - self.pcr_overbought)
            
            confluence = (rsi_distance + pcr_distance) / 2
            confidence = min(100, confluence * 100 * min_confluence_strength)
            
            reasons.append(f"✅ RSI {rsi:.1f} > {self.rsi_overbought} (overbought)")
            reasons.append(f"✅ PCR {pcr:.2f} > {self.pcr_overbought} (bearish)")
            reasons.append(f"Confluence strength: {confluence:.2%}")
        
        # NO SIGNAL cases
        else:
            if rsi >= self.rsi_oversold and rsi <= self.rsi_overbought:
                reasons.append(f"RSI {rsi:.1f} in neutral zone ({self.rsi_oversold}-{self.rsi_overbought})")
            elif rsi < self.rsi_oversold:
                reasons.append(f"✅ RSI {rsi:.1f} oversold, but PCR {pcr:.2f} not bullish")
            else:
                reasons.append(f"✅ RSI {rsi:.1f} overbought, but PCR {pcr:.2f} not bearish")
        
        return DirectionalSignal(
            signal=signal,
            confidence=confidence,
            rsi=rsi,
            pcr=pcr,
            rsi_percentile=rsi_percentile,
            pcr_percentile=pcr_percentile,
            reasons=reasons
        )
    
    def _calculate_pcr_percentile(self, pcr: float) -> float:
        """
        Convert PCR value to percentile (0=bearish, 1=bullish).
        
        Args:
            pcr: PCR value
            
        Returns:
            Percentile 0-1 (where 0.5 is neutral ~1.0 PCR)
        """
        # Typical PCR range is 0.5 to 2.0
        # Below 0.7 = bullish, above 1.3 = bearish
        # Normalize with sigmoid-like curve
        
        neutral_pcr = 1.0
        if pcr < neutral_pcr:
            # Bullish side: PCR 0.5 → 1.0
            percentile = 0.5 + (0.5 * (pcr - 0.5) / (neutral_pcr - 0.5))
        else:
            # Bearish side: PCR 1.0 → 2.0
            percentile = 0.5 - (0.5 * (pcr - neutral_pcr) / (2.0 - neutral_pcr))
        
        return np.clip(percentile, 0.0, 1.0)
    
    def get_signal_summary(self, signal: DirectionalSignal) -> str:
        """
        Format signal for display.
        
        Args:
            signal: DirectionalSignal object
            
        Returns:
            Formatted string for UI display
        """
        emoji = {
            "CALL_BUY": "📈",
            "PUT_BUY": "📉",
            "NO_SIGNAL": "🔕"
        }
        
        lines = [
            f"{emoji.get(signal.signal, '❓')} {signal.signal}",
            f"Confidence: {signal.confidence:.0f}%",
            f"RSI: {signal.rsi:.1f}" if signal.rsi else "RSI: N/A",
            f"PCR: {signal.pcr:.2f}" if signal.pcr else "PCR: N/A",
        ]
        
        if signal.reasons:
            lines.append("Reasons:")
            for reason in signal.reasons:
                lines.append(f"  {reason}")
        
        return "\n".join(lines)

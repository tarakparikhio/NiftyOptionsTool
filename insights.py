"""
Insights Module for Options Analytics Dashboard

Generates rule-based textual insights and alerts based on positioning data.
Focus on helping discretionary traders understand:
- Where smart money is building
- Whether writers are defending higher or lower levels
- If volatility is shifting structurally
- If positioning is confirming price moves
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from metrics import OptionsMetrics, MultiWeekMetrics


class InsightsEngine:
    """
    Generates actionable insights from options positioning data.
    """
    
    def __init__(self, weekly_data: Dict[str, pd.DataFrame], current_week: str):
        """
        Initialize insights engine.
        
        Args:
            weekly_data: Dictionary mapping week names to DataFrames
            current_week: Name of the current/latest week
        """
        self.weekly_data = weekly_data
        self.current_week = current_week
        self.weeks = sorted(weekly_data.keys())
        self.insights = []
        
    def generate_all_insights(self, expiry: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Generate all insights for the current week.
        
        Args:
            expiry: Specific expiry to analyze (None for all)
            
        Returns:
            List of insight dictionaries with category, message, and severity
        """
        self.insights = []
        
        # Get current and previous week data
        current_df = self.weekly_data[self.current_week].copy()
        if expiry:
            current_df = current_df[current_df['Expiry'] == expiry]
        
        current_metrics = OptionsMetrics(current_df)
        
        # Generate various insights
        self._analyze_pcr(current_metrics, expiry)
        self._analyze_oi_concentration(current_metrics)
        self._analyze_iv_skew(current_metrics)
        self._analyze_strike_migration()
        self._analyze_ce_pe_dominance(current_metrics)
        self._analyze_support_resistance(current_metrics)
        
        # Multi-week trend analysis
        if len(self.weeks) > 1:
            self._analyze_trends()
        
        return self.insights
    
    def _add_insight(self, category: str, message: str, severity: str = 'INFO',
                    signal: Optional[str] = None):
        """
        Add an insight to the list.
        
        Args:
            category: Category of insight (e.g., 'PCR', 'OI_SHIFT', 'IV')
            message: The insight message
            severity: 'INFO', 'WARNING', 'CRITICAL'
            signal: Optional signal ('BULLISH', 'BEARISH', 'NEUTRAL')
        """
        self.insights.append({
            'category': category,
            'message': message,
            'severity': severity,
            'signal': signal or 'NEUTRAL'
        })
    
    def _analyze_pcr(self, metrics: OptionsMetrics, expiry: Optional[str] = None):
        """
        Analyze PCR and generate insights.
        """
        pcr_df = metrics.compute_pcr(by_expiry=False)
        if pcr_df.empty:
            return
        
        pcr = pcr_df['PCR'].iloc[0]
        pe_oi = pcr_df.get('PE_OI', pd.Series([0])).iloc[0]
        ce_oi = pcr_df.get('CE_OI', pd.Series([0])).iloc[0]
        
        # Check week-over-week PCR change if available
        pcr_change = None
        if len(self.weeks) > 1:
            prev_week = self.weeks[-2]
            prev_df = self.weekly_data[prev_week]
            if expiry:
                prev_df = prev_df[prev_df['Expiry'] == expiry]
            prev_metrics = OptionsMetrics(prev_df)
            prev_pcr_df = prev_metrics.compute_pcr(by_expiry=False)
            if not prev_pcr_df.empty:
                prev_pcr = prev_pcr_df['PCR'].iloc[0]
                pcr_change = pcr - prev_pcr
        
        # PCR interpretations
        if pcr > 1.5:
            self._add_insight(
                'PCR',
                f'⚠️ EXTREME Put dominance (PCR: {pcr:.2f}). Heavy Put buying suggests strong bearish hedging or directional bearish view. Watch for unwinding.',
                'CRITICAL',
                'BEARISH'
            )
        elif pcr > 1.3:
            self._add_insight(
                'PCR',
                f'📉 High PCR ({pcr:.2f}) indicates Put buildup. Market participants positioning for downside or buying protection.',
                'WARNING',
                'BEARISH'
            )
        elif pcr < 0.5:
            self._add_insight(
                'PCR',
                f'⚠️ EXTREME Call dominance (PCR: {pcr:.2f}). Heavy Call buying suggests strong bullish positioning. Watch for profit booking.',
                'CRITICAL',
                'BULLISH'
            )
        elif pcr < 0.7:
            self._add_insight(
                'PCR',
                f'📈 Low PCR ({pcr:.2f}) indicates Call buildup. Bullish positioning or reduction in Put hedges.',
                'WARNING',
                'BULLISH'
            )
        else:
            self._add_insight(
                'PCR',
                f'➡️ Balanced PCR ({pcr:.2f}). Market in equilibrium. No strong directional bias from options positioning.',
                'INFO',
                'NEUTRAL'
            )
        
        # Analyze PCR change
        if pcr_change is not None:
            if abs(pcr_change) > 0.3:
                direction = 'RISING' if pcr_change > 0 else 'FALLING'
                sentiment = 'BEARISH' if pcr_change > 0 else 'BULLISH'
                self._add_insight(
                    'PCR_CHANGE',
                    f'🔄 Major PCR shift: {direction} by {abs(pcr_change):.2f}. Significant change in positioning sentiment ({sentiment} shift).',
                    'WARNING',
                    sentiment
                )
    
    def _analyze_oi_concentration(self, metrics: OptionsMetrics):
        """
        Analyze OI concentration and its implications.
        """
        concentration = metrics.compute_oi_concentration(top_n=3)
        ratio = concentration['concentration_ratio']
        
        if ratio > 50:
            self._add_insight(
                'OI_CONCENTRATION',
                f'🎯 High OI concentration ({ratio:.1f}% in top 3 strikes). Market strongly anchored at key levels. Breakout may be explosive.',
                'WARNING',
                'NEUTRAL'
            )
        elif ratio > 35:
            self._add_insight(
                'OI_CONCENTRATION',
                f'📍 Moderate OI concentration ({ratio:.1f}%). Clear defense levels established.',
                'INFO',
                'NEUTRAL'
            )
        else:
            self._add_insight(
                'OI_CONCENTRATION',
                f'🌊 Dispersed OI ({ratio:.1f}% in top strikes). Lack of strong conviction at specific levels. Range-bound behavior likely.',
                'INFO',
                'NEUTRAL'
            )
        
        # Analyze CE vs PE concentration difference
        ce_conc = concentration['ce_concentration']
        pe_conc = concentration['pe_concentration']
        
        if abs(ce_conc - pe_conc) > 15:
            if ce_conc > pe_conc:
                self._add_insight(
                    'OI_CONCENTRATION',
                    f'☝️ Call writers more concentrated ({ce_conc:.1f}%) than Put writers ({pe_conc:.1f}%). Strong upside resistance capping rallies.',
                    'INFO',
                    'BEARISH'
                )
            else:
                self._add_insight(
                    'OI_CONCENTRATION',
                    f'👇 Put writers more concentrated ({pe_conc:.1f}%) than Call writers ({ce_conc:.1f}%). Strong downside support preventing selloffs.',
                    'INFO',
                    'BULLISH'
                )
    
    def _analyze_iv_skew(self, metrics: OptionsMetrics):
        """
        Analyze IV skew patterns.
        """
        skew = metrics.compute_iv_skew()
        if not skew:
            return
        
        atm_otm_skew = skew.get('ATM_OTM_Skew', 0)
        atm_iv = skew.get('ATM_IV', 0)
        
        if atm_otm_skew > 3:
            self._add_insight(
                'IV_SKEW',
                f'📊 Positive IV skew ({atm_otm_skew:.2f}). ATM options trading at premium to OTM. Heightened near-term uncertainty.',
                'INFO',
                'NEUTRAL'
            )
        elif atm_otm_skew < -3:
            self._add_insight(
                'IV_SKEW',
                f'📊 Negative IV skew ({atm_otm_skew:.2f}). OTM options expensive relative to ATM. Tail risk hedging active.',
                'WARNING',
                'BEARISH'
            )
        
        # Check IV levels
        if atm_iv > 20:
            self._add_insight(
                'IV_LEVEL',
                f'⚡ Elevated IV ({atm_iv:.1f}%). Uncertainty priced in. Good for sellers, expensive for buyers.',
                'INFO',
                'NEUTRAL'
            )
        elif atm_iv < 12:
            self._add_insight(
                'IV_LEVEL',
                f'😌 Low IV ({atm_iv:.1f}%). Complacency evident. Cheap options for hedging but limited premium for sellers.',
                'INFO',
                'NEUTRAL'
            )
    
    def _analyze_strike_migration(self):
        """
        Analyze if strikes are migrating up or down over weeks.
        """
        if len(self.weeks) < 2:
            return
        
        # Get OI shift data from current and previous week
        current_df = self.weekly_data[self.current_week]
        current_metrics = OptionsMetrics(current_df)
        shift = current_metrics.detect_oi_shift_direction()
        
        ce_shift = shift.get('ce_shift', 'UNKNOWN')
        pe_shift = shift.get('pe_shift', 'UNKNOWN')
        
        # Interpret shifts
        if ce_shift == 'UP' and pe_shift == 'UP':
            self._add_insight(
                'OI_MIGRATION',
                '⬆️ Both Call and Put OI migrating UPWARD. Market repricing higher equilibrium. Bullish structural shift.',
                'WARNING',
                'BULLISH'
            )
        elif ce_shift == 'DOWN' and pe_shift == 'DOWN':
            self._add_insight(
                'OI_MIGRATION',
                '⬇️ Both Call and Put OI migrating DOWNWARD. Market repricing lower equilibrium. Bearish structural shift.',
                'WARNING',
                'BEARISH'
            )
        elif ce_shift == 'UP' and pe_shift == 'DOWN':
            self._add_insight(
                'OI_MIGRATION',
                '🔀 Divergent migration: Calls up, Puts down. Call writers defending higher while Put support weakening. Mixed signals.',
                'INFO',
                'NEUTRAL'
            )
        elif ce_shift == 'DOWN' and pe_shift == 'UP':
            self._add_insight(
                'OI_MIGRATION',
                '🔀 Divergent migration: Calls down, Puts up. Call resistance easing while Put support building. Cautiously bullish.',
                'INFO',
                'BULLISH'
            )
    
    def _analyze_ce_pe_dominance(self, metrics: OptionsMetrics):
        """
        Analyze CE/PE dominance patterns.
        """
        dominance = metrics.compute_ce_pe_dominance(by_expiry=False)
        if dominance.empty:
            return
        
        oi_dom = dominance['OI_Dominance'].iloc[0]
        vol_dom = dominance['Volume_Dominance'].iloc[0]
        
        ce_oi = dominance.get('OI_CE', pd.Series([0])).iloc[0]
        pe_oi = dominance.get('OI_PE', pd.Series([0])).iloc[0]
        ce_vol = dominance.get('Volume_CE', pd.Series([0])).iloc[0]
        pe_vol = dominance.get('Volume_PE', pd.Series([0])).iloc[0]
        
        # Check if OI and Volume dominance agree
        if oi_dom == vol_dom:
            if oi_dom == 'CE':
                self._add_insight(
                    'DOMINANCE',
                    f'🟢 Call dominance in both OI and Volume. Active Call positioning. Writers capping upside or buyers betting on rally.',
                    'INFO',
                    'NEUTRAL'
                )
            else:
                self._add_insight(
                    'DOMINANCE',
                    f'🔴 Put dominance in both OI and Volume. Active Put positioning. Hedging in play or bearish directional bets.',
                    'INFO',
                    'NEUTRAL'
                )
        else:
            self._add_insight(
                'DOMINANCE',
                f'⚖️ Mixed signals: OI favors {oi_dom}, Volume favors {vol_dom}. Short-term activity diverging from longer-term positioning.',
                'WARNING',
                'NEUTRAL'
            )
    
    def _analyze_support_resistance(self, metrics: OptionsMetrics):
        """
        Identify key support and resistance from OI.
        """
        levels = metrics.get_support_resistance_levels(top_n=3)
        max_pain = metrics.compute_max_pain()
        
        support = levels['support']
        resistance = levels['resistance']
        
        if support:
            support_str = ', '.join([f"{s:.0f}" for s in support[:3]])
            self._add_insight(
                'SUPPORT',
                f'🛡️ Key Put OI support levels: {support_str}. Strong Put writing at these strikes indicates defense zones.',
                'INFO',
                'NEUTRAL'
            )
        
        if resistance:
            resist_str = ', '.join([f"{r:.0f}" for r in resistance[:3]])
            self._add_insight(
                'RESISTANCE',
                f'🚧 Key Call OI resistance levels: {resist_str}. Strong Call writing suggests upside capping.',
                'INFO',
                'NEUTRAL'
            )
        
        if max_pain > 0:
            self._add_insight(
                'MAX_PAIN',
                f'🎯 Max Pain at {max_pain:.0f}. This is where option sellers lose least. Gravitational pull towards this level near expiry.',
                'INFO',
                'NEUTRAL'
            )
    
    def _analyze_trends(self):
        """
        Analyze multi-week trends.
        """
        if len(self.weeks) < 3:
            return
        
        multi_metrics = MultiWeekMetrics(self.weekly_data)
        
        # Check for consecutive weeks of OI migration
        recent_weeks = self.weeks[-3:]
        shifts = []
        
        for week in recent_weeks:
            df = self.weekly_data[week]
            metrics = OptionsMetrics(df)
            shift = metrics.detect_oi_shift_direction()
            shifts.append(shift)
        
        # Check if CE shifts are consistently in same direction
        ce_shifts = [s.get('ce_shift') for s in shifts]
        pe_shifts = [s.get('pe_shift') for s in shifts]
        
        if ce_shifts.count('UP') >= 2:
            self._add_insight(
                'TREND',
                f'📈 Call writers retreating upward for {ce_shifts.count("UP")} consecutive weeks. Sustained bullish pressure evident.',
                'WARNING',
                'BULLISH'
            )
        elif ce_shifts.count('DOWN') >= 2:
            self._add_insight(
                'TREND',
                f'📉 Call writers moving down for {ce_shifts.count("DOWN")} consecutive weeks. Bearish structural shift in progress.',
                'WARNING',
                'BEARISH'
            )
    
    def generate_summary(self) -> str:
        """
        Generate a textual summary of all insights.
        
        Returns:
            Formatted string with all insights
        """
        if not self.insights:
            return "No insights generated."
        
        summary_lines = [f"\n{'='*60}"]
        summary_lines.append(f"POSITIONING INTELLIGENCE - {self.current_week}")
        summary_lines.append(f"{'='*60}\n")
        
        # Group by severity
        critical = [i for i in self.insights if i['severity'] == 'CRITICAL']
        warnings = [i for i in self.insights if i['severity'] == 'WARNING']
        infos = [i for i in self.insights if i['severity'] == 'INFO']
        
        if critical:
            summary_lines.append("🚨 CRITICAL ALERTS:")
            for insight in critical:
                summary_lines.append(f"  • {insight['message']}")
            summary_lines.append("")
        
        if warnings:
            summary_lines.append("⚠️  IMPORTANT OBSERVATIONS:")
            for insight in warnings:
                summary_lines.append(f"  • {insight['message']}")
            summary_lines.append("")
        
        if infos:
            summary_lines.append("ℹ️  ADDITIONAL INSIGHTS:")
            for insight in infos:
                summary_lines.append(f"  • {insight['message']}")
            summary_lines.append("")
        
        # Overall signal
        bullish_count = sum(1 for i in self.insights if i['signal'] == 'BULLISH')
        bearish_count = sum(1 for i in self.insights if i['signal'] == 'BEARISH')
        
        summary_lines.append(f"{'='*60}")
        summary_lines.append(f"OVERALL SIGNAL SCORE: {bullish_count} Bullish | {bearish_count} Bearish")
        
        if bullish_count > bearish_count + 2:
            summary_lines.append("Verdict: 📈 NET BULLISH positioning")
        elif bearish_count > bullish_count + 2:
            summary_lines.append("Verdict: 📉 NET BEARISH positioning")
        else:
            summary_lines.append("Verdict: ↔️  NEUTRAL / MIXED signals")
        
        summary_lines.append(f"{'='*60}\n")
        
        return '\n'.join(summary_lines)


if __name__ == "__main__":
    # Test insights generation
    from data_loader import OptionsDataLoader
    
    loader = OptionsDataLoader("/Users/tarak/Documents/AIPlayGround/Trading/Options/Monthly")
    weekly_data = loader.load_all_weeks()
    
    if weekly_data:
        # Add derived columns to all weeks
        for week in weekly_data:
            weekly_data[week] = loader.add_derived_columns(weekly_data[week])
        
        latest_week = loader.get_latest_week()
        engine = InsightsEngine(weekly_data, latest_week)
        
        insights = engine.generate_all_insights()
        summary = engine.generate_summary()
        
        print(summary)

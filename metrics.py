"""
Metrics Module for Options Analytics Dashboard

Computes structural positioning metrics:
- OI concentration and distribution
- PCR (Put-Call Ratio)
- IV skew analysis
- Strike migration patterns
- Max Pain calculation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional


class OptionsMetrics:
    """
    Computes positioning intelligence metrics from option chain data.
    Focus on structural changes rather than price prediction.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with option chain DataFrame.
        
        Args:
            df: DataFrame with columns: Strike, Option_Type, OI, IV, Volume, etc.
        """
        self.df = df.copy()
        
    def compute_pcr(self, by_expiry: bool = True) -> pd.DataFrame:
        """
        Compute Put-Call Ratio (OI based).
        
        Args:
            by_expiry: If True, compute PCR for each expiry separately
            
        Returns:
            DataFrame with PCR values
        """
        if by_expiry and 'Expiry' in self.df.columns:
            group_cols = ['Expiry']
        else:
            group_cols = []
        
        # Separate CE and PE
        ce_df = self.df[self.df['Option_Type'] == 'CE'].copy()
        pe_df = self.df[self.df['Option_Type'] == 'PE'].copy()
        
        if group_cols:
            ce_oi = ce_df.groupby(group_cols)['OI'].sum().reset_index()
            pe_oi = pe_df.groupby(group_cols)['OI'].sum().reset_index()
            
            pcr_df = pd.merge(pe_oi, ce_oi, on=group_cols, suffixes=('_PE', '_CE'))
            pcr_df['PCR'] = pcr_df['OI_PE'] / (pcr_df['OI_CE'] + 1)
        else:
            total_pe_oi = pe_df['OI'].sum()
            total_ce_oi = ce_df['OI'].sum()
            pcr_df = pd.DataFrame([{
                'PCR': total_pe_oi / (total_ce_oi + 1),
                'PE_OI': total_pe_oi,
                'CE_OI': total_ce_oi
            }])
        
        return pcr_df
    
    def get_top_oi_strikes(self, n: int = 5, by_type: bool = True) -> pd.DataFrame:
        """
        Get top N strikes by OI build-up.
        
        Args:
            n: Number of top strikes to return
            by_type: If True, get top N for CE and PE separately
            
        Returns:
            DataFrame with top OI strikes
        """
        if by_type:
            ce_top = (self.df[self.df['Option_Type'] == 'CE']
                     .nlargest(n, 'OI')[['Strike', 'OI', 'OI_Change', 'Volume', 'IV']])
            ce_top['Type'] = 'CE'
            
            pe_top = (self.df[self.df['Option_Type'] == 'PE']
                     .nlargest(n, 'OI')[['Strike', 'OI', 'OI_Change', 'Volume', 'IV']])
            pe_top['Type'] = 'PE'
            
            return pd.concat([ce_top, pe_top], ignore_index=True)
        else:
            return self.df.nlargest(n, 'OI')[['Strike', 'Option_Type', 'OI', 
                                               'OI_Change', 'Volume', 'IV']]
    
    def compute_oi_concentration(self, top_n: int = 3) -> Dict[str, float]:
        """
        Compute OI concentration ratio.
        Shows how concentrated positioning is at key strikes.
        
        Args:
            top_n: Number of top strikes to consider
            
        Returns:
            Dictionary with concentration metrics
        """
        total_oi = self.df['OI'].sum()
        
        # Top N strikes total OI
        top_strikes = self.df.nlargest(top_n, 'OI')
        top_oi = top_strikes['OI'].sum()
        
        # Concentration ratio
        concentration_ratio = (top_oi / total_oi * 100) if total_oi > 0 else 0
        
        # Separate by type
        ce_total = self.df[self.df['Option_Type'] == 'CE']['OI'].sum()
        pe_total = self.df[self.df['Option_Type'] == 'PE']['OI'].sum()
        
        ce_top = (self.df[self.df['Option_Type'] == 'CE']
                 .nlargest(top_n, 'OI')['OI'].sum())
        pe_top = (self.df[self.df['Option_Type'] == 'PE']
                 .nlargest(top_n, 'OI')['OI'].sum())
        
        return {
            'concentration_ratio': concentration_ratio,
            'top_n_strikes': top_n,
            'top_oi': top_oi,
            'total_oi': total_oi,
            'ce_concentration': (ce_top / ce_total * 100) if ce_total > 0 else 0,
            'pe_concentration': (pe_top / pe_total * 100) if pe_total > 0 else 0
        }
    
    def compute_iv_skew(self) -> Dict[str, float]:
        """
        Compute IV skew metrics.
        
        Returns:
            Dictionary with skew metrics for ATM, ITM, OTM
        """
        if 'Moneyness' not in self.df.columns:
            return {}
        
        # Get average IV by moneyness
        iv_by_moneyness = self.df.groupby('Moneyness')['IV'].mean().to_dict()
        
        atm_iv = iv_by_moneyness.get('ATM', 0)
        otm_iv = iv_by_moneyness.get('OTM', 0)
        itm_iv = iv_by_moneyness.get('ITM', 0)
        
        # Calculate skew
        skew = {
            'ATM_IV': atm_iv,
            'OTM_IV': otm_iv,
            'ITM_IV': itm_iv,
            'ATM_OTM_Skew': atm_iv - otm_iv,
            'ATM_ITM_Skew': atm_iv - itm_iv
        }
        
        return skew
    
    def compute_ce_pe_dominance(self, by_expiry: bool = True) -> pd.DataFrame:
        """
        Compute CE/PE dominance by OI and Volume.
        
        Args:
            by_expiry: If True, compute for each expiry
            
        Returns:
            DataFrame showing which side is dominant
        """
        group_cols = ['Expiry'] if by_expiry and 'Expiry' in self.df.columns else []
        
        if group_cols:
            grouped = self.df.groupby(group_cols + ['Option_Type']).agg({
                'OI': 'sum',
                'Volume': 'sum',
                'OI_Change': 'sum'
            }).reset_index()
            
            # Pivot to get CE and PE side by side
            result = grouped.pivot_table(
                index=group_cols,
                columns='Option_Type',
                values=['OI', 'Volume', 'OI_Change']
            ).reset_index()
            
            # Flatten column names
            result.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                            for col in result.columns.values]
            
            # Calculate dominance
            result['OI_Dominance'] = np.where(
                result.get('OI_CE', 0) > result.get('OI_PE', 0), 'CE', 'PE'
            )
            result['Volume_Dominance'] = np.where(
                result.get('Volume_CE', 0) > result.get('Volume_PE', 0), 'CE', 'PE'
            )
        else:
            ce_metrics = self.df[self.df['Option_Type'] == 'CE'].agg({
                'OI': 'sum',
                'Volume': 'sum',
                'OI_Change': 'sum'
            })
            pe_metrics = self.df[self.df['Option_Type'] == 'PE'].agg({
                'OI': 'sum',
                'Volume': 'sum',
                'OI_Change': 'sum'
            })
            
            result = pd.DataFrame([{
                'OI_CE': ce_metrics['OI'],
                'OI_PE': pe_metrics['OI'],
                'Volume_CE': ce_metrics['Volume'],
                'Volume_PE': pe_metrics['Volume'],
                'OI_Change_CE': ce_metrics['OI_Change'],
                'OI_Change_PE': pe_metrics['OI_Change'],
                'OI_Dominance': 'CE' if ce_metrics['OI'] > pe_metrics['OI'] else 'PE',
                'Volume_Dominance': 'CE' if ce_metrics['Volume'] > pe_metrics['Volume'] else 'PE'
            }])
        
        return result
    
    def detect_oi_shift_direction(self) -> Dict[str, any]:
        """
        Detect if OI is shifting up or down in strikes.
        Analyzes weighted average strike movement.
        
        Returns:
            Dictionary with shift metrics
        """
        # Calculate weighted average strike by OI
        ce_df = self.df[self.df['Option_Type'] == 'CE'].copy()
        pe_df = self.df[self.df['Option_Type'] == 'PE'].copy()
        
        # Weighted average strike
        ce_weighted_strike = (ce_df['Strike'] * ce_df['OI']).sum() / (ce_df['OI'].sum() + 1)
        pe_weighted_strike = (pe_df['Strike'] * pe_df['OI']).sum() / (pe_df['OI'].sum() + 1)
        
        # OI change weighted average
        ce_chg_weighted = (ce_df['Strike'] * ce_df['OI_Change']).sum() / (ce_df['OI_Change'].abs().sum() + 1)
        pe_chg_weighted = (pe_df['Strike'] * pe_df['OI_Change']).sum() / (pe_df['OI_Change'].abs().sum() + 1)
        
        return {
            'ce_weighted_strike': ce_weighted_strike,
            'pe_weighted_strike': pe_weighted_strike,
            'ce_new_oi_weighted_strike': ce_chg_weighted,
            'pe_new_oi_weighted_strike': pe_chg_weighted,
            'ce_shift': 'UP' if ce_chg_weighted > ce_weighted_strike else 'DOWN',
            'pe_shift': 'UP' if pe_chg_weighted > pe_weighted_strike else 'DOWN'
        }
    
    def compute_max_pain(self) -> float:
        """
        Compute Max Pain strike.
        The strike where option writers (sellers) lose the least money.
        
        Returns:
            Max Pain strike price
        """
        # Get unique strikes
        strikes = sorted(self.df['Strike'].unique())
        
        max_pain_value = float('inf')
        max_pain_strike = strikes[len(strikes) // 2] if strikes else 0
        
        for strike in strikes:
            # Calculate total loss for option writers at this strike
            # For Calls: loss if strike < expiry price
            ce_loss = self.df[
                (self.df['Option_Type'] == 'CE') & 
                (self.df['Strike'] < strike)
            ]['OI'].sum() * 50  # Lot size approximation
            
            # For Puts: loss if strike > expiry price
            pe_loss = self.df[
                (self.df['Option_Type'] == 'PE') & 
                (self.df['Strike'] > strike)
            ]['OI'].sum() * 50
            
            total_loss = ce_loss + pe_loss
            
            if total_loss < max_pain_value:
                max_pain_value = total_loss
                max_pain_strike = strike
        
        return max_pain_strike
    
    def get_support_resistance_levels(self, top_n: int = 5) -> Dict[str, List[float]]:
        """
        Identify key support and resistance levels based on OI.
        
        Args:
            top_n: Number of levels to identify
            
        Returns:
            Dictionary with support and resistance strikes
        """
        # PE OI indicates support (puts being bought/sold)
        pe_df = self.df[self.df['Option_Type'] == 'PE'].copy()
        support_levels = (pe_df.nlargest(top_n, 'OI')['Strike']
                         .sort_values()
                         .tolist())
        
        # CE OI indicates resistance (calls being bought/sold)
        ce_df = self.df[self.df['Option_Type'] == 'CE'].copy()
        resistance_levels = (ce_df.nlargest(top_n, 'OI')['Strike']
                           .sort_values()
                           .tolist())
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    def compute_oi_distribution_stats(self) -> Dict[str, any]:
        """
        Compute statistical distribution metrics for OI.
        
        Returns:
            Dictionary with distribution statistics
        """
        ce_df = self.df[self.df['Option_Type'] == 'CE']
        pe_df = self.df[self.df['Option_Type'] == 'PE']
        
        return {
            'total_oi': self.df['OI'].sum(),
            'ce_total_oi': ce_df['OI'].sum(),
            'pe_total_oi': pe_df['OI'].sum(),
            'total_volume': self.df['Volume'].sum(),
            'ce_volume': ce_df['Volume'].sum(),
            'pe_volume': pe_df['Volume'].sum(),
            'avg_iv': self.df['IV'].mean(),
            'ce_avg_iv': ce_df['IV'].mean(),
            'pe_avg_iv': pe_df['IV'].mean(),
            'oi_std': self.df['OI'].std(),
            'oi_skew': self.df['OI'].skew() if len(self.df) > 2 else 0
        }


class MultiWeekMetrics:
    """
    Analyzes metrics across multiple weeks to identify trends.
    """
    
    def __init__(self, weekly_data: Dict[str, pd.DataFrame]):
        """
        Initialize with weekly data dictionary.
        
        Args:
            weekly_data: Dict mapping week names to DataFrames
        """
        self.weekly_data = weekly_data
        self.weeks = sorted(weekly_data.keys())
    
    def compute_pcr_trend(self, expiry: Optional[str] = None) -> pd.DataFrame:
        """
        Compute PCR trend across weeks.
        
        Args:
            expiry: Specific expiry to filter (None for all)
            
        Returns:
            DataFrame with PCR values per week
        """
        pcr_data = []
        
        for week in self.weeks:
            df = self.weekly_data[week]
            if expiry:
                df = df[df['Expiry'] == expiry]
            
            metrics = OptionsMetrics(df)
            pcr_df = metrics.compute_pcr(by_expiry=False)
            
            pcr_data.append({
                'Week': week,
                'PCR': pcr_df['PCR'].iloc[0] if not pcr_df.empty else 0,
                'PE_OI': pcr_df.get('PE_OI', [0]).iloc[0] if not pcr_df.empty else 0,
                'CE_OI': pcr_df.get('CE_OI', [0]).iloc[0] if not pcr_df.empty else 0
            })
        
        return pd.DataFrame(pcr_data)
    
    def track_strike_migration(self, top_n: int = 3) -> pd.DataFrame:
        """
        Track top OI strikes across weeks.
        
        Args:
            top_n: Number of top strikes to track
            
        Returns:
            DataFrame showing strike movement over time
        """
        migration_data = []
        
        for week in self.weeks:
            df = self.weekly_data[week]
            metrics = OptionsMetrics(df)
            top_strikes = metrics.get_top_oi_strikes(n=top_n, by_type=True)
            
            for _, row in top_strikes.iterrows():
                migration_data.append({
                    'Week': week,
                    'Strike': row['Strike'],
                    'Type': row['Type'],
                    'OI': row['OI'],
                    'Rank': _
                })
        
        return pd.DataFrame(migration_data)
    
    def detect_regime_shifts(self) -> List[Dict[str, any]]:
        """
        Detect major regime shifts in positioning.
        
        Returns:
            List of detected regime shifts
        """
        shifts = []
        pcr_trend = self.compute_pcr_trend()
        
        if len(pcr_trend) < 2:
            return shifts
        
        for i in range(1, len(pcr_trend)):
            prev_pcr = pcr_trend.iloc[i-1]['PCR']
            curr_pcr = pcr_trend.iloc[i]['PCR']
            week = pcr_trend.iloc[i]['Week']
            
            # Detect significant PCR changes
            if curr_pcr > 1.3 and prev_pcr <= 1.3:
                shifts.append({
                    'week': week,
                    'type': 'BEARISH_SHIFT',
                    'reason': 'PCR crossed above 1.3 - Heavy Put buildup',
                    'pcr': curr_pcr
                })
            elif curr_pcr < 0.7 and prev_pcr >= 0.7:
                shifts.append({
                    'week': week,
                    'type': 'BULLISH_SHIFT',
                    'reason': 'PCR dropped below 0.7 - Heavy Call buildup',
                    'pcr': curr_pcr
                })
            elif abs(curr_pcr - prev_pcr) > 0.3:
                direction = 'UP' if curr_pcr > prev_pcr else 'DOWN'
                shifts.append({
                    'week': week,
                    'type': 'MAJOR_PCR_CHANGE',
                    'reason': f'PCR moved {direction} by {abs(curr_pcr - prev_pcr):.2f}',
                    'pcr': curr_pcr
                })
        
        return shifts


if __name__ == "__main__":
    # Test metrics computation
    from data_loader import OptionsDataLoader
    
    loader = OptionsDataLoader("/Users/tarak/Documents/AIPlayGround/Trading/Options/Monthly")
    loader.load_all_weeks()
    
    latest_week = loader.get_latest_week()
    if latest_week:
        df = loader.get_data_for_week(latest_week)
        
        metrics = OptionsMetrics(df)
        
        print("\n=== PCR Analysis ===")
        print(metrics.compute_pcr())
        
        print("\n=== Top OI Strikes ===")
        print(metrics.get_top_oi_strikes())
        
        print("\n=== OI Concentration ===")
        print(metrics.compute_oi_concentration())
        
        print("\n=== IV Skew ===")
        print(metrics.compute_iv_skew())
        
        print("\n=== Max Pain ===")
        print(f"Max Pain Strike: {metrics.compute_max_pain()}")
        
        print("\n=== Support/Resistance ===")
        print(metrics.get_support_resistance_levels())

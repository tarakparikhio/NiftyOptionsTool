"""
Historical vs Present Comparison Engine

Computes week-over-week and day-over-day delta metrics.
Provides statistical context for current positioning.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats


class ComparisonEngine:
    """
    Analyzes structural changes in positioning over time.
    """
    
    def __init__(self, weekly_data: Dict[str, pd.DataFrame]):
        """
        Initialize comparison engine.
        
        Args:
            weekly_data: Dictionary mapping week names to DataFrames
        """
        self.weekly_data = weekly_data
        self.weeks = sorted(weekly_data.keys())
        
    def compute_wow_changes(self, current_week: str, previous_week: str) -> pd.DataFrame:
        """
        Compute week-over-week changes.
        
        Args:
            current_week: Current week identifier
            previous_week: Previous week identifier
            
        Returns:
            DataFrame with WoW changes
        """
        if current_week not in self.weekly_data or previous_week not in self.weekly_data:
            return pd.DataFrame()
        
        curr_df = self.weekly_data[current_week]
        prev_df = self.weekly_data[previous_week]
        
        # Merge on Strike, Option_Type, Expiry
        merged = pd.merge(
            prev_df[['Strike', 'Option_Type', 'Expiry', 'OI', 'IV', 'Volume']],
            curr_df[['Strike', 'Option_Type', 'Expiry', 'OI', 'IV', 'Volume']],
            on=['Strike', 'Option_Type', 'Expiry'],
            suffixes=('_prev', '_curr'),
            how='outer'
        ).fillna(0)
        
        # Calculate percentage changes
        merged['OI_Change_Pct'] = ((merged['OI_curr'] - merged['OI_prev']) / 
                                   (merged['OI_prev'] + 1)) * 100
        merged['OI_Change_Abs'] = merged['OI_curr'] - merged['OI_prev']
        
        merged['IV_Change_Pct'] = ((merged['IV_curr'] - merged['IV_prev']) / 
                                   (merged['IV_prev'] + 0.01)) * 100
        merged['IV_Change_Abs'] = merged['IV_curr'] - merged['IV_prev']
        
        merged['Volume_Change_Pct'] = ((merged['Volume_curr'] - merged['Volume_prev']) / 
                                       (merged['Volume_prev'] + 1)) * 100
        
        merged['Week_From'] = previous_week
        merged['Week_To'] = current_week
        
        return merged
    
    def get_max_oi_shifts(self, comparison_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        Get strikes with maximum OI shifts.
        
        Args:
            comparison_df: DataFrame from compute_wow_changes
            top_n: Number of top shifts to return
            
        Returns:
            DataFrame with top OI shifts
        """
        # Sort by absolute OI change
        shifts = comparison_df.copy()
        shifts['OI_Change_Abs_Magnitude'] = shifts['OI_Change_Abs'].abs()
        
        top_shifts = shifts.nlargest(top_n, 'OI_Change_Abs_Magnitude')
        
        return top_shifts[['Strike', 'Option_Type', 'Expiry', 
                          'OI_prev', 'OI_curr', 'OI_Change_Abs', 'OI_Change_Pct']]
    
    def compute_pcr_evolution(self) -> pd.DataFrame:
        """
        Compute PCR evolution over all weeks.
        
        Returns:
            DataFrame with PCR for each week
        """
        pcr_data = []
        
        for week in self.weeks:
            df = self.weekly_data[week]
            
            ce_oi = df[df['Option_Type'] == 'CE']['OI'].sum()
            pe_oi = df[df['Option_Type'] == 'PE']['OI'].sum()
            
            pcr = pe_oi / (ce_oi + 1)
            
            pcr_data.append({
                'Week': week,
                'PCR': pcr,
                'PE_OI': pe_oi,
                'CE_OI': ce_oi
            })
        
        pcr_df = pd.DataFrame(pcr_data)
        
        # Add moving average
        pcr_df['PCR_MA_3'] = pcr_df['PCR'].rolling(window=3, min_periods=1).mean()
        
        return pcr_df
    
    def compute_iv_evolution(self, expiry: Optional[str] = None) -> pd.DataFrame:
        """
        Compute IV evolution over time.
        
        Args:
            expiry: Filter by specific expiry
            
        Returns:
            DataFrame with IV metrics per week
        """
        iv_data = []
        
        for week in self.weeks:
            df = self.weekly_data[week].copy()
            
            if expiry:
                df = df[df['Expiry'] == expiry]
            
            if df.empty:
                continue
            
            iv_data.append({
                'Week': week,
                'Mean_IV': df['IV'].mean(),
                'Median_IV': df['IV'].median(),
                'Std_IV': df['IV'].std(),
                'Max_IV': df['IV'].max(),
                'Min_IV': df['IV'].min(),
                'CE_Mean_IV': df[df['Option_Type'] == 'CE']['IV'].mean(),
                'PE_Mean_IV': df[df['Option_Type'] == 'PE']['IV'].mean()
            })
        
        return pd.DataFrame(iv_data)
    
    def detect_strike_migration_pattern(self, lookback_weeks: int = 4) -> Dict:
        """
        Detect if strikes are consistently migrating up or down.
        
        Args:
            lookback_weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with migration analysis
        """
        if len(self.weeks) < lookback_weeks:
            lookback_weeks = len(self.weeks)
        
        recent_weeks = self.weeks[-lookback_weeks:]
        
        ce_weighted_strikes = []
        pe_weighted_strikes = []
        
        for week in recent_weeks:
            df = self.weekly_data[week]
            
            # Calculate weighted average strikes
            ce_df = df[df['Option_Type'] == 'CE']
            pe_df = df[df['Option_Type'] == 'PE']
            
            if not ce_df.empty:
                ce_weighted = (ce_df['Strike'] * ce_df['OI']).sum() / (ce_df['OI'].sum() + 1)
                ce_weighted_strikes.append(ce_weighted)
            
            if not pe_df.empty:
                pe_weighted = (pe_df['Strike'] * pe_df['OI']).sum() / (pe_df['OI'].sum() + 1)
                pe_weighted_strikes.append(pe_weighted)
        
        # Analyze trend
        ce_trend = 'UP' if len(ce_weighted_strikes) > 1 and ce_weighted_strikes[-1] > ce_weighted_strikes[0] else 'DOWN'
        pe_trend = 'UP' if len(pe_weighted_strikes) > 1 and pe_weighted_strikes[-1] > pe_weighted_strikes[0] else 'DOWN'
        
        # Calculate trend strength (linear regression slope)
        ce_slope = 0
        pe_slope = 0
        
        if len(ce_weighted_strikes) > 1:
            x = np.arange(len(ce_weighted_strikes))
            ce_slope, _ = np.polyfit(x, ce_weighted_strikes, 1)
        
        if len(pe_weighted_strikes) > 1:
            x = np.arange(len(pe_weighted_strikes))
            pe_slope, _ = np.polyfit(x, pe_weighted_strikes, 1)
        
        return {
            'ce_trend': ce_trend,
            'pe_trend': pe_trend,
            'ce_slope': ce_slope,
            'pe_slope': pe_slope,
            'ce_strikes': ce_weighted_strikes,
            'pe_strikes': pe_weighted_strikes,
            'weeks': recent_weeks
        }
    
    def compute_z_scores(self, current_week: str) -> Dict:
        """
        Compute Z-scores for current week metrics relative to historical distribution.
        
        Args:
            current_week: Week to analyze
            
        Returns:
            Dictionary with Z-scores
        """
        if current_week not in self.weekly_data:
            return {}
        
        current_df = self.weekly_data[current_week]
        
        # Compute historical distributions
        all_oi = []
        all_iv = []
        all_pcr = []
        
        for week in self.weeks[:-1]:  # Exclude current week from historical
            df = self.weekly_data[week]
            all_oi.append(df['OI'].mean())
            all_iv.append(df['IV'].mean())
            
            ce_oi = df[df['Option_Type'] == 'CE']['OI'].sum()
            pe_oi = df[df['Option_Type'] == 'PE']['OI'].sum()
            all_pcr.append(pe_oi / (ce_oi + 1))
        
        # Current metrics
        current_oi = current_df['OI'].mean()
        current_iv = current_df['IV'].mean()
        
        ce_oi = current_df[current_df['Option_Type'] == 'CE']['OI'].sum()
        pe_oi = current_df[current_df['Option_Type'] == 'PE']['OI'].sum()
        current_pcr = pe_oi / (ce_oi + 1)
        
        # Calculate Z-scores
        z_scores = {}
        
        if len(all_oi) > 1:
            z_scores['oi_zscore'] = (current_oi - np.mean(all_oi)) / (np.std(all_oi) + 0.001)
        
        if len(all_iv) > 1:
            z_scores['iv_zscore'] = (current_iv - np.mean(all_iv)) / (np.std(all_iv) + 0.001)
        
        if len(all_pcr) > 1:
            z_scores['pcr_zscore'] = (current_pcr - np.mean(all_pcr)) / (np.std(all_pcr) + 0.001)
        
        z_scores['current_oi'] = current_oi
        z_scores['current_iv'] = current_iv
        z_scores['current_pcr'] = current_pcr
        
        return z_scores
    
    def get_comparison_summary(self, current_week: str) -> Dict:
        """
        Generate comprehensive comparison summary.
        
        Args:
            current_week: Week to analyze
            
        Returns:
            Dictionary with comparison metrics
        """
        if current_week not in self.weekly_data:
            return {}
        
        current_idx = self.weeks.index(current_week)
        
        summary = {
            'current_week': current_week,
            'total_weeks_available': len(self.weeks)
        }
        
        # WoW comparison
        if current_idx > 0:
            previous_week = self.weeks[current_idx - 1]
            wow_changes = self.compute_wow_changes(current_week, previous_week)
            
            summary['wow_max_oi_gain'] = wow_changes['OI_Change_Abs'].max()
            summary['wow_max_oi_loss'] = wow_changes['OI_Change_Abs'].min()
            summary['wow_mean_iv_change'] = wow_changes['IV_Change_Abs'].mean()
        
        # Z-scores
        z_scores = self.compute_z_scores(current_week)
        summary.update(z_scores)
        
        # Migration pattern
        migration = self.detect_strike_migration_pattern()
        summary['migration_ce_trend'] = migration['ce_trend']
        summary['migration_pe_trend'] = migration['pe_trend']
        
        # PCR evolution
        pcr_evolution = self.compute_pcr_evolution()
        if not pcr_evolution.empty:
            current_pcr_row = pcr_evolution[pcr_evolution['Week'] == current_week]
            if not current_pcr_row.empty:
                summary['pcr'] = current_pcr_row['PCR'].iloc[0]
                summary['pcr_ma_3'] = current_pcr_row['PCR_MA_3'].iloc[0]
        
        return summary


if __name__ == "__main__":
    # Test comparison engine
    from utils.io_helpers import OptionsDataLoader
    
    loader = OptionsDataLoader("data/raw/monthly")
    weekly_data = loader.load_all_weeks()
    
    if weekly_data:
        # Add derived columns
        for week in weekly_data:
            weekly_data[week] = loader.add_derived_columns(weekly_data[week])
        
        engine = ComparisonEngine(weekly_data)
        
        print("\n=== PCR Evolution ===")
        pcr_evolution = engine.compute_pcr_evolution()
        print(pcr_evolution)
        
        print("\n=== Strike Migration ===")
        migration = engine.detect_strike_migration_pattern()
        print(f"CE Trend: {migration['ce_trend']}, Slope: {migration['ce_slope']:.2f}")
        print(f"PE Trend: {migration['pe_trend']}, Slope: {migration['pe_slope']:.2f}")
        
        if len(engine.weeks) > 1:
            current = engine.weeks[-1]
            print(f"\n=== Comparison Summary for {current} ===")
            summary = engine.get_comparison_summary(current)
            for key, value in summary.items():
                print(f"{key}: {value}")

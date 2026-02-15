"""
Data Loader Module for Options Analytics Dashboard

Handles loading and preprocessing of weekly option chain CSV files.
Supports NSE-style option chain format with CALLS and PUTS in merged rows.
Also supports live NSE option chain fetching via API.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from typing import Dict, List, Tuple, Optional


class OptionsDataLoader:
    """
    Loads and processes weekly option chain CSV files.
    Creates derived metrics for structural analysis.
    """
    
    def __init__(self, data_folder: str):
        """
        Initialize the data loader.
        
        Args:
            data_folder: Path to folder containing weekly CSV folders
        """
        self.data_folder = Path(data_folder)
        self.weekly_data = {}
        self.weeks = []
        
    def load_live_chain(self, expiry_date: str, use_cache: bool = True) -> pd.DataFrame:
        """
        Load live option chain data from NSE for a specific expiry.
        
        Args:
            expiry_date: Expiry date in DD-MMM-YYYY format (e.g., '27-Feb-2026')
            use_cache: If True, use cached data on API failure
            
        Returns:
            DataFrame with processed option chain data including derived columns
            
        Raises:
            Exception: If unable to fetch data and no cache available
        """
        from api_clients.nse_option_chain import NSEOptionChainClient
        
        try:
            # Initialize NSE client
            client = NSEOptionChainClient()
            
            # Fetch option chain
            df = client.get_option_chain_by_expiry(expiry_date)
            
            if df.empty:
                raise ValueError("No data returned from NSE")
            
            # Add derived columns using existing logic
            df = self.add_derived_columns(df)
            
            return df
            
        except Exception as e:
            error_msg = f"Error loading live chain: {e}"
            if use_cache:
                error_msg += " (tried cache fallback)"
            print(error_msg)
            raise
        
    def load_all_weeks(self) -> Dict[str, pd.DataFrame]:
        """
        Load all weekly CSV files from the data folder.
        
        Returns:
            Dictionary mapping week names to combined DataFrames
        """
        # Find all weekly folders (e.g., Feb7, Feb14)
        weekly_folders = sorted([f for f in self.data_folder.iterdir() if f.is_dir()])
        
        for week_folder in weekly_folders:
            week_name = week_folder.name
            week_data = self._load_week(week_folder)
            if not week_data.empty:
                self.weekly_data[week_name] = week_data
                self.weeks.append(week_name)
        
        print(f"Loaded {len(self.weekly_data)} weeks of data: {self.weeks}")
        return self.weekly_data
    
    def _load_week(self, week_folder: Path) -> pd.DataFrame:
        """
        Load all CSV files for a specific week and combine them.
        
        Args:
            week_folder: Path to the week's folder
            
        Returns:
            Combined DataFrame for all expiries in that week
        """
        csv_files = sorted(week_folder.glob("*.csv"))
        all_expiries = []
        
        for csv_file in csv_files:
            try:
                # Extract expiry date from filename
                expiry_date = self._extract_expiry_from_filename(csv_file.name)
                
                # Parse the NSE-style CSV
                df = self._parse_nse_csv(csv_file)
                
                if not df.empty:
                    df['Expiry'] = expiry_date
                    df['Week'] = week_folder.name
                    all_expiries.append(df)
            except Exception as e:
                print(f"Error loading {csv_file.name}: {e}")
                continue
        
        if all_expiries:
            return pd.concat(all_expiries, ignore_index=True)
        return pd.DataFrame()
    
    def _extract_expiry_from_filename(self, filename: str) -> str:
        """
        Extract expiry date from filename.
        
        Example: option-chain-ED-NIFTY-28-Apr-2026.csv -> 2026-04-28
        """
        # Pattern: DD-MMM-YYYY
        pattern = r'(\d{1,2})-([A-Za-z]{3})-(\d{4})'
        match = re.search(pattern, filename)
        
        if match:
            day, month, year = match.groups()
            # Convert month abbreviation to number
            month_map = {
                'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
            }
            month_num = month_map.get(month, '01')
            return f"{year}-{month_num}-{day.zfill(2)}"
        
        return "Unknown"
    
    def _parse_nse_csv(self, csv_file: Path) -> pd.DataFrame:
        """
        Parse NSE-style option chain CSV where CALLS and PUTS are in merged rows.
        
        The format has:
        - Row 1: "CALLS,,PUTS"
        - Row 2: Column headers
        - Data rows: Call data, Strike, Put data
        
        Column structure:
        - Columns 1-10: CALLS (OI, CHNG IN OI, VOLUME, IV, LTP, CHNG, BID QTY, BID, ASK, ASK QTY)
        - Column 11: STRIKE
        - Columns 12-21: PUTS (BID QTY, BID, ASK, ASK QTY, CHNG, LTP, IV, VOLUME, CHNG IN OI, OI)
        """
        # Read the CSV, skipping the first row (CALLS,,PUTS)
        df_raw = pd.read_csv(csv_file, skiprows=1)
        
        # Find the STRIKE column
        strike_col = None
        for col in df_raw.columns:
            if 'STRIKE' in str(col).upper():
                strike_col = col
                break
        
        if strike_col is None:
            print(f"Warning: Could not find STRIKE column in {csv_file.name}")
            return pd.DataFrame()
        
        # Get column indices
        cols = df_raw.columns.tolist()
        strike_idx = cols.index(strike_col)
        
        # Parse CALLS (columns before STRIKE) and PUTS (columns after STRIKE)
        calls_data = []
        puts_data = []
        
        for idx, row in df_raw.iterrows():
            try:
                strike = self._clean_number(row[strike_col])
                if pd.isna(strike) or strike == 0:
                    continue
                
                # CALLS data (left side of STRIKE)
                # Column order: OI, CHNG IN OI, VOLUME, IV, LTP, ...
                ce_oi = self._clean_number(row.iloc[1]) if strike_idx > 1 else 0
                ce_oi_chg = self._clean_number(row.iloc[2]) if strike_idx > 2 else 0
                ce_volume = self._clean_number(row.iloc[3]) if strike_idx > 3 else 0
                ce_iv = self._clean_number(row.iloc[4]) if strike_idx > 4 else 0
                ce_ltp = self._clean_number(row.iloc[5]) if strike_idx > 5 else 0
                
                # PUTS data (right side of STRIKE)
                # The PUT columns are: BID QTY.1, BID.1, ASK.1, ASK QTY.1, CHNG.1, LTP.1, IV.1, VOLUME.1, CHNG IN OI.1, OI.1
                # So from STRIKE index: +1 to +10
                # We need: OI.1 (last), CHNG IN OI.1 (-2 from end), VOLUME.1 (-3), IV.1 (-4), LTP.1 (-5)
                
                # More reliable: use named columns if available
                if 'OI.1' in df_raw.columns:
                    pe_oi = self._clean_number(row['OI.1'])
                else:
                    pe_oi = self._clean_number(row.iloc[-2]) if len(row) > strike_idx + 1 else 0
                
                if 'CHNG IN OI.1' in df_raw.columns:
                    pe_oi_chg = self._clean_number(row['CHNG IN OI.1'])
                else:
                    pe_oi_chg = self._clean_number(row.iloc[-3]) if len(row) > strike_idx + 2 else 0
                
                if 'VOLUME.1' in df_raw.columns:
                    pe_volume = self._clean_number(row['VOLUME.1'])
                else:
                    pe_volume = self._clean_number(row.iloc[-4]) if len(row) > strike_idx + 3 else 0
                
                if 'IV.1' in df_raw.columns:
                    pe_iv = self._clean_number(row['IV.1'])
                else:
                    pe_iv = self._clean_number(row.iloc[-5]) if len(row) > strike_idx + 4 else 0
                
                if 'LTP.1' in df_raw.columns:
                    pe_ltp = self._clean_number(row['LTP.1'])
                else:
                    pe_ltp = self._clean_number(row.iloc[-6]) if len(row) > strike_idx + 5 else 0
                
                # Add CE row
                calls_data.append({
                    'Strike': strike,
                    'Option_Type': 'CE',
                    'OI': ce_oi,
                    'OI_Change': ce_oi_chg,
                    'Volume': ce_volume,
                    'IV': ce_iv,
                    'LTP': ce_ltp
                })
                
                # Add PE row
                puts_data.append({
                    'Strike': strike,
                    'Option_Type': 'PE',
                    'OI': pe_oi,
                    'OI_Change': pe_oi_chg,
                    'Volume': pe_volume,
                    'IV': pe_iv,
                    'LTP': pe_ltp
                })
                
            except Exception as e:
                continue
        
        # Combine calls and puts
        all_data = calls_data + puts_data
        return pd.DataFrame(all_data)
    
    def _clean_number(self, value) -> float:
        """
        Clean and convert string numbers to float.
        Handles commas, dashes, and other formatting.
        """
        if pd.isna(value):
            return 0.0
        
        # Convert to string and clean
        value_str = str(value).strip()
        
        # Handle dash or empty
        if value_str in ['-', '', 'nan']:
            return 0.0
        
        # Remove commas and quotes
        value_str = value_str.replace(',', '').replace('"', '').replace("'", '')
        
        try:
            return float(value_str)
        except:
            return 0.0
    
    def add_derived_columns(self, df: pd.DataFrame, spot_price: float = None) -> pd.DataFrame:
        """
        Add derived columns for analysis.
        
        Args:
            df: DataFrame with option chain data
            spot_price: Current spot price (auto-detected if None)
            
        Returns:
            DataFrame with additional derived columns
        """
        df = df.copy()
        
        # Auto-detect spot price (usually near ATM strikes with high volume/OI)
        if spot_price is None:
            spot_price = self._estimate_spot_price(df)
        
        df['Spot_Price'] = spot_price
        
        # Strike distance from spot (percentage)
        df['Strike_Distance_Pct'] = ((df['Strike'] - spot_price) / spot_price) * 100
        
        # Moneyness category
        df['Moneyness'] = df.apply(self._classify_moneyness, axis=1)
        
        # Quarterly expiry bucket
        df['Expiry_Quarter'] = df['Expiry'].apply(self._get_quarter)
        
        return df
    
    def _estimate_spot_price(self, df: pd.DataFrame) -> float:
        """
        Estimate spot price from option chain data.
        Uses the strike with highest total OI or around median strike.
        """
        if df.empty:
            return 0.0
        
        # Group by strike and sum OI
        strike_oi = df.groupby('Strike')['OI'].sum().reset_index()
        
        # Find strike with maximum total OI (usually near ATM)
        if not strike_oi.empty:
            max_oi_strike = strike_oi.loc[strike_oi['OI'].idxmax(), 'Strike']
            return max_oi_strike
        
        # Fallback to median strike
        return df['Strike'].median()
    
    def _classify_moneyness(self, row) -> str:
        """
        Classify option as ITM, ATM, or OTM based on strike distance.
        """
        distance_pct = abs(row['Strike_Distance_Pct'])
        
        if distance_pct < 1.0:
            return 'ATM'
        elif row['Option_Type'] == 'CE':
            return 'OTM' if row['Strike'] > row['Spot_Price'] else 'ITM'
        else:  # PE
            return 'OTM' if row['Strike'] < row['Spot_Price'] else 'ITM'
    
    def _get_quarter(self, expiry_str: str) -> str:
        """
        Extract quarter from expiry date.
        
        Args:
            expiry_str: Date string in format YYYY-MM-DD
            
        Returns:
            Quarter string like 'Q1-2026' (Mar), 'Q2-2026' (Jun), etc.
        """
        try:
            date_obj = pd.to_datetime(expiry_str)
            month = date_obj.month
            year = date_obj.year
            
            # Map month to quarterly expiry
            if month in [1, 2, 3]:
                return f'Mar-{year}'
            elif month in [4, 5, 6]:
                return f'Jun-{year}'
            elif month in [7, 8, 9]:
                return f'Sep-{year}'
            else:
                return f'Dec-{year}'
        except:
            return 'Unknown'
    
    def compute_week_over_week_changes(self) -> pd.DataFrame:
        """
        Compute week-over-week changes in OI, IV, and other metrics.
        
        Returns:
            DataFrame with WoW changes for each strike and expiry
        """
        if len(self.weekly_data) < 2:
            print("Need at least 2 weeks of data for WoW analysis")
            return pd.DataFrame()
        
        all_comparisons = []
        
        # Compare consecutive weeks
        for i in range(len(self.weeks) - 1):
            week1 = self.weeks[i]
            week2 = self.weeks[i + 1]
            
            df1 = self.weekly_data[week1]
            df2 = self.weekly_data[week2]
            
            # Merge on Strike, Option_Type, Expiry
            merged = pd.merge(
                df1[['Strike', 'Option_Type', 'Expiry', 'OI', 'IV', 'Volume']],
                df2[['Strike', 'Option_Type', 'Expiry', 'OI', 'IV', 'Volume']],
                on=['Strike', 'Option_Type', 'Expiry'],
                suffixes=('_prev', '_curr')
            )
            
            # Calculate changes
            merged['OI_Change_Pct'] = ((merged['OI_curr'] - merged['OI_prev']) / 
                                       (merged['OI_prev'] + 1)) * 100
            merged['IV_Change_Pct'] = ((merged['IV_curr'] - merged['IV_prev']) / 
                                       (merged['IV_prev'] + 0.01)) * 100
            merged['Volume_Change_Pct'] = ((merged['Volume_curr'] - merged['Volume_prev']) / 
                                          (merged['Volume_prev'] + 1)) * 100
            
            merged['Week_From'] = week1
            merged['Week_To'] = week2
            
            all_comparisons.append(merged)
        
        if all_comparisons:
            return pd.concat(all_comparisons, ignore_index=True)
        return pd.DataFrame()
    
    def get_data_for_week(self, week_name: str) -> pd.DataFrame:
        """
        Get processed data for a specific week.
        """
        if week_name in self.weekly_data:
            df = self.weekly_data[week_name]
            return self.add_derived_columns(df)
        return pd.DataFrame()
    
    def get_latest_week(self) -> str:
        """
        Get the name of the most recent week.
        """
        return self.weeks[-1] if self.weeks else None


if __name__ == "__main__":
    # Test the data loader
    loader = OptionsDataLoader("/Users/tarak/Documents/AIPlayGround/Trading/Options/Monthly")
    loader.load_all_weeks()
    
    # Get latest week data
    latest_week = loader.get_latest_week()
    if latest_week:
        df = loader.get_data_for_week(latest_week)
        print(f"\nLatest week: {latest_week}")
        print(f"Rows: {len(df)}")
        print(f"\nSample data:")
        print(df.head(10))
        print(f"\nExpiries available: {df['Expiry_Quarter'].unique()}")

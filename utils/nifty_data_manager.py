"""
NIFTY Data Cleanup and Update Utility

Cleans downloaded NSE CSV files and maintains nifty_close.csv
Supports daily incremental updates
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


class NiftyDataManager:
    """Manage NIFTY historical data"""
    
    def __init__(self, data_dir: str = "data/reference"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.target_file = self.data_dir / "nifty_close.csv"
    
    def clean_csv(self, input_file: str) -> pd.DataFrame:
        """
        Clean downloaded NSE CSV file.
        
        Args:
            input_file: Path to downloaded CSV
            
        Returns:
            Cleaned DataFrame
        """
        df = pd.read_csv(input_file)
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Ensure required columns exist
        required_cols = ['Date', 'Open', 'High', 'Low', 'Close']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"CSV must have columns: {required_cols}")
        
        # Convert date to datetime
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y', errors='coerce')
        
        # Remove rows with invalid dates or missing OHLC
        df = df.dropna(subset=['Date', 'Open', 'High', 'Low', 'Close'])
        
        # Sort chronologically (oldest first)
        df = df.sort_values('Date', ascending=True)
        
        # Remove duplicates (keep most recent)
        df = df.drop_duplicates(subset=['Date'], keep='last')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def merge_with_existing(self, new_df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge new data with existing, removing duplicates.
        
        Args:
            new_df: New DataFrame to merge
            
        Returns:
            Combined DataFrame
        """
        if self.target_file.exists():
            # Load existing data
            existing_df = pd.read_csv(self.target_file)
            existing_df['Date'] = pd.to_datetime(existing_df['Date'])
            
            # Combine
            combined = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Remove duplicates (keep new data)
            combined = combined.drop_duplicates(subset=['Date'], keep='last')
            
            # Sort chronologically
            combined = combined.sort_values('Date', ascending=True)
            combined = combined.reset_index(drop=True)
            
            print(f"📊 Merged: {len(existing_df)} existing + {len(new_df)} new = {len(combined)} total rows")
            
            return combined
        else:
            print(f"📊 New file: {len(new_df)} rows")
            return new_df
    
    def add_daily_update(self, date_str: str, open_val: float, high: float, 
                         low: float, close: float, volume: int = 0, 
                         turnover: float = 0.0):
        """
        Add single day's data.
        
        Args:
            date_str: Date in 'DD-MMM-YYYY' or 'YYYY-MM-DD' format
            open_val: Opening price
            high: High price
            low: Low price
            close: Closing price
            volume: Volume (optional)
            turnover: Turnover (optional)
        """
        # Parse date
        try:
            date = pd.to_datetime(date_str, format='%d-%b-%Y')
        except:
            date = pd.to_datetime(date_str)
        
        # Create single row DataFrame
        new_row = pd.DataFrame([{
            'Date': date,
            'Open': open_val,
            'High': high,
            'Low': low,
            'Close': close,
            'Shares Traded': volume,
            'Turnover (₹ Cr)': turnover
        }])
        
        # Merge with existing
        combined = self.merge_with_existing(new_row)
        
        # Save
        self.save(combined)
        
        print(f"✅ Added data for {date.strftime('%d-%b-%Y')}")
    
    def save(self, df: pd.DataFrame):
        """
        Save DataFrame to nifty_close.csv.
        
        Args:
            df: DataFrame to save
        """
        # Format date as string for CSV
        df_save = df.copy()
        df_save['Date'] = df_save['Date'].dt.strftime('%d-%b-%Y')
        
        # Save
        df_save.to_csv(self.target_file, index=False)
        
        print(f"💾 Saved to: {self.target_file}")
        print(f"📅 Date range: {df['Date'].min().strftime('%d-%b-%Y')} to {df['Date'].max().strftime('%d-%b-%Y')}")
        print(f"📊 Total rows: {len(df)}")
    
    def process_downloaded_file(self, input_file: str, merge: bool = True):
        """
        Main processing pipeline.
        
        Args:
            input_file: Path to downloaded CSV
            merge: If True, merge with existing data; if False, replace
        """
        print(f"🔄 Processing: {input_file}")
        
        # Clean CSV
        df_clean = self.clean_csv(input_file)
        
        print(f"✅ Cleaned: {len(df_clean)} valid rows")
        
        # Merge or replace
        if merge:
            df_final = self.merge_with_existing(df_clean)
        else:
            df_final = df_clean
            print(f"⚠️ Replacing existing data")
        
        # Save
        self.save(df_final)
        
        return df_final
    
    def get_summary(self):
        """Print summary of current data"""
        if not self.target_file.exists():
            print("❌ No data file found")
            return
        
        df = pd.read_csv(self.target_file)
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
        
        print("=" * 60)
        print("NIFTY DATA SUMMARY")
        print("=" * 60)
        print(f"📁 File: {self.target_file}")
        print(f"📊 Rows: {len(df)}")
        print(f"📅 Start: {df['Date'].min().strftime('%d-%b-%Y')}")
        print(f"📅 End: {df['Date'].max().strftime('%d-%b-%Y')}")
        print(f"📈 Latest Close: {df['Close'].iloc[-1]:,.2f}")
        print(f"📉 52-Week High: {df['High'].max():,.2f}")
        print(f"📉 52-Week Low: {df['Low'].min():,.2f}")
        print("=" * 60)


def quick_cleanup(input_file: str = "data/reference/NIFTY 50-14-02-2025-to-14-02-2026.csv"):
    """Quick cleanup of default downloaded file"""
    manager = NiftyDataManager()
    manager.process_downloaded_file(input_file, merge=False)
    manager.get_summary()


def add_today(open_val: float, high: float, low: float, close: float, volume: int = 0):
    """Quick add today's data"""
    manager = NiftyDataManager()
    today = datetime.now().strftime('%d-%b-%Y')
    manager.add_daily_update(today, open_val, high, low, close, volume)


if __name__ == "__main__":
    # Example: Process downloaded file
    quick_cleanup()

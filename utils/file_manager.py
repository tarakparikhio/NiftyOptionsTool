"""
File Manager Module

Handles CSV file upload, cleaning, organization, and auto-saving
into structured folders based on expiry type (weekly/monthly).
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Optional
import re
import calendar


class FileManager:
    """
    Manages CSV file uploads and organization.
    
    Features:
    - Filename cleaning and standardization
    - Weekly vs Monthly expiry detection
    - Structured folder creation
    - Auto-saving uploaded files
    """
    
    def __init__(self, base_dir: str = "data/raw"):
        """
        Initialize File Manager.
        
        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def clean_filename(self, original_name: str) -> str:
        """
        Clean and standardize filename.
        
        Extracts symbol and expiry, standardizes format to:
        NIFTY_<EXPIRY>_<YYYYMMDD>.csv
        
        Args:
            original_name: Original uploaded filename
            
        Returns:
            Cleaned standardized filename
            
        Example:
            "option-chain-ED-NIFTY-28-Apr-2026.csv" 
            -> "NIFTY_28Apr2026_20260214.csv"
        """
        # Extract expiry date pattern: DD-MMM-YYYY
        expiry_pattern = r'(\d{1,2})-([A-Za-z]{3})-(\d{4})'
        match = re.search(expiry_pattern, original_name)
        
        if match:
            day, month, year = match.groups()
            # Standardize format: DDMMMYYYY (e.g., 28Apr2026)
            expiry_str = f"{day.zfill(2)}{month.capitalize()}{year}"
        else:
            # Fallback: use timestamp
            expiry_str = "UnknownExpiry"
        
        # Get current date for filename
        today = datetime.now().strftime("%Y%m%d")
        
        # Standardized format
        cleaned = f"NIFTY_{expiry_str}_{today}.csv"
        
        return cleaned
        
    def extract_expiry_date(self, filename: str) -> Optional[datetime]:
        """
        Extract expiry date from filename.
        
        Args:
            filename: CSV filename
            
        Returns:
            Datetime object of expiry date, or None if not found
        """
        # Pattern: DD-MMM-YYYY or DDMMMYYYY
        patterns = [
            r'(\d{1,2})-([A-Za-z]{3})-(\d{4})',  # 28-Apr-2026
            r'(\d{2})([A-Za-z]{3})(\d{4})',       # 28Apr2026
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                day, month_str, year = match.groups()
                
                # Map month abbreviation to number
                month_map = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                
                month = month_map.get(month_str.capitalize())
                if month:
                    try:
                        return datetime(int(year), month, int(day))
                    except ValueError:
                        continue
        
        return None
        
    def determine_weekly_or_monthly(self, expiry_date: datetime) -> str:
        """
        Determine if expiry is weekly or monthly.
        
        Logic: Monthly expiry = last Thursday of the month
        
        Args:
            expiry_date: Expiry datetime object
            
        Returns:
            "monthly" or "weekly"
        """
        # Get last day of the month
        last_day = calendar.monthrange(expiry_date.year, expiry_date.month)[1]
        
        # Find last Thursday
        last_thursday = None
        for day in range(last_day, 0, -1):
            date_obj = datetime(expiry_date.year, expiry_date.month, day)
            if date_obj.weekday() == 3:  # Thursday = 3
                last_thursday = date_obj
                break
        
        # Check if expiry is the last Thursday
        if last_thursday and expiry_date.date() == last_thursday.date():
            return "monthly"
        else:
            return "weekly"
            
    def save_uploaded_file(self, file_bytes: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Save uploaded file to structured folder.
        
        Steps:
        1. Clean filename
        2. Extract expiry date
        3. Determine weekly/monthly
        4. Create folder: data/raw/{weekly|monthly}/{YYYY-MM-DD}/
        5. Save file
        
        Args:
            file_bytes: Raw file bytes
            original_filename: Original uploaded filename
            
        Returns:
            Tuple of (saved_path, folder_type)
            
        Raises:
            ValueError: If expiry date cannot be extracted
        """
        # Clean filename
        cleaned_filename = self.clean_filename(original_filename)
        
        # Extract expiry date
        expiry_date = self.extract_expiry_date(original_filename)
        if expiry_date is None:
            raise ValueError(f"Could not extract expiry date from filename: {original_filename}")
        
        # Determine weekly or monthly
        folder_type = self.determine_weekly_or_monthly(expiry_date)
        
        # Create folder structure: data/raw/{weekly|monthly}/{YYYY-MM-DD}/
        today = datetime.now().strftime("%Y-%m-%d")
        target_folder = self.base_dir / folder_type / today
        target_folder.mkdir(parents=True, exist_ok=True)
        
        # Save file
        target_path = target_folder / cleaned_filename
        target_path.write_bytes(file_bytes)
        
        return str(target_path), folder_type
        
    def list_available_dates(self, folder_type: str = "monthly") -> list:
        """
        List available date folders.
        
        Args:
            folder_type: "monthly" or "weekly"
            
        Returns:
            List of date strings (YYYY-MM-DD) in descending order
        """
        folder_path = self.base_dir / folder_type
        if not folder_path.exists():
            return []
        
        dates = []
        for item in folder_path.iterdir():
            if item.is_dir():
                # Validate date format
                try:
                    datetime.strptime(item.name, "%Y-%m-%d")
                    dates.append(item.name)
                except ValueError:
                    continue
        
        return sorted(dates, reverse=True)
        
    def get_files_for_date(self, date_str: str, folder_type: str = "monthly") -> list:
        """
        Get all CSV files for a specific date.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            folder_type: "monthly" or "weekly"
            
        Returns:
            List of Path objects for CSV files
        """
        folder_path = self.base_dir / folder_type / date_str
        if not folder_path.exists():
            return []
        
        return sorted(folder_path.glob("*.csv"))


if __name__ == "__main__":
    # Test the file manager
    fm = FileManager()
    
    # Test filename cleaning
    test_names = [
        "option-chain-ED-NIFTY-28-Apr-2026.csv",
        "option-chain-ED-NIFTY-30-Jun-2026.csv",
        "NIFTY_Weekly_20Feb2026.csv"
    ]
    
    print("=== Filename Cleaning ===")
    for name in test_names:
        cleaned = fm.clean_filename(name)
        print(f"{name} -> {cleaned}")
    
    print("\n=== Expiry Detection ===")
    for name in test_names:
        expiry = fm.extract_expiry_date(name)
        if expiry:
            folder_type = fm.determine_weekly_or_monthly(expiry)
            print(f"{name} -> {expiry.date()} ({folder_type})")
    
    print("\n=== Available Dates ===")
    for folder_type in ["monthly", "weekly"]:
        dates = fm.list_available_dates(folder_type)
        print(f"{folder_type.capitalize()}: {dates}")

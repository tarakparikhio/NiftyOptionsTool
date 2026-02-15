"""
Date and Time Utilities for Options Analytics

Handles date parsing, expiry calculations, and time-based filtering.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Optional


def parse_expiry_from_filename(filename: str) -> Optional[str]:
    """
    Extract expiry date from filename.
    
    Args:
        filename: e.g., 'option-chain-ED-NIFTY-28-Apr-2026.csv'
        
    Returns:
        Date string in YYYY-MM-DD format or None
    """
    import re
    pattern = r'(\d{1,2})-([A-Za-z]{3})-(\d{4})'
    match = re.search(pattern, filename)
    
    if match:
        day, month, year = match.groups()
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        month_num = month_map.get(month, '01')
        return f"{year}-{month_num}-{day.zfill(2)}"
    
    return None


def get_quarter_from_date(date_str: str) -> str:
    """
    Get quarterly expiry label from date.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Quarter label like 'Mar-2026', 'Jun-2026', etc.
    """
    try:
        date_obj = pd.to_datetime(date_str)
        month = date_obj.month
        year = date_obj.year
        
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


def get_expiry_type(date_str: str) -> str:
    """
    Determine if expiry is monthly, quarterly, or weekly.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        'WEEKLY', 'MONTHLY', or 'QUARTERLY'
    """
    try:
        date_obj = pd.to_datetime(date_str)
        day = date_obj.day
        month = date_obj.month
        
        # Quarterly expiries are last Thursday of Mar, Jun, Sep, Dec
        if month in [3, 6, 9, 12]:
            # Check if it's last Thursday
            last_day = pd.Timestamp(year=date_obj.year, month=month, day=1) + pd.offsets.MonthEnd(1)
            last_thursday = last_day - pd.Timedelta(days=(last_day.dayofweek - 3) % 7)
            
            if date_obj.date() == last_thursday.date():
                return 'QUARTERLY'
        
        # Monthly expiries are last Thursday of each month
        if day > 21:  # Likely last Thursday
            return 'MONTHLY'
        
        return 'WEEKLY'
    except:
        return 'UNKNOWN'


def get_days_to_expiry(expiry_date: str, from_date: Optional[str] = None) -> int:
    """
    Calculate days until expiry.
    
    Args:
        expiry_date: Expiry date in YYYY-MM-DD format
        from_date: Reference date (default: today)
        
    Returns:
        Number of days to expiry
    """
    try:
        expiry = pd.to_datetime(expiry_date)
        reference = pd.to_datetime(from_date) if from_date else pd.Timestamp.now()
        return (expiry - reference).days
    except:
        return 0


def get_trading_days_between(start_date: str, end_date: str) -> int:
    """
    Get number of trading days between two dates (excluding weekends).
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        Number of trading days
    """
    try:
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        # Generate business days
        trading_days = pd.bdate_range(start, end)
        return len(trading_days)
    except:
        return 0


def format_week_label(date_str: str) -> str:
    """
    Format date into week label for display.
    
    Args:
        date_str: Date string
        
    Returns:
        Week label like 'Feb7', 'Feb14', etc.
    """
    try:
        date_obj = pd.to_datetime(date_str)
        month = date_obj.strftime('%b')
        day = date_obj.day
        return f"{month}{day}"
    except:
        return date_str


def get_nearest_expiry(reference_date: str, expiry_list: List[str]) -> Optional[str]:
    """
    Find the nearest expiry date from a list.
    
    Args:
        reference_date: Reference date in YYYY-MM-DD format
        expiry_list: List of expiry dates
        
    Returns:
        Nearest expiry date or None
    """
    if not expiry_list:
        return None
    
    try:
        ref = pd.to_datetime(reference_date)
        expiries = [pd.to_datetime(e) for e in expiry_list]
        
        # Find nearest future expiry
        future_expiries = [e for e in expiries if e >= ref]
        if future_expiries:
            nearest = min(future_expiries, key=lambda x: abs((x - ref).days))
            return nearest.strftime('%Y-%m-%d')
        
        return None
    except:
        return None


def get_week_range(date_str: str) -> Tuple[str, str]:
    """
    Get the Monday-Friday range for a given date's week.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        Tuple of (monday_date, friday_date) as strings
    """
    try:
        date_obj = pd.to_datetime(date_str)
        
        # Get Monday of the week
        monday = date_obj - timedelta(days=date_obj.weekday())
        
        # Get Friday of the week
        friday = monday + timedelta(days=4)
        
        return (monday.strftime('%Y-%m-%d'), friday.strftime('%Y-%m-%d'))
    except:
        return (date_str, date_str)


def is_expiry_week(date_str: str, expiry_date: str) -> bool:
    """
    Check if a date falls in the expiry week.
    
    Args:
        date_str: Date to check
        expiry_date: Expiry date
        
    Returns:
        True if date is in expiry week
    """
    try:
        date_obj = pd.to_datetime(date_str)
        expiry_obj = pd.to_datetime(expiry_date)
        
        # Get week ranges
        date_monday, date_friday = get_week_range(date_str)
        expiry_monday, expiry_friday = get_week_range(expiry_date)
        
        return date_monday == expiry_monday
    except:
        return False


def generate_utc_timestamp() -> str:
    """
    Generate UTC timestamp for file naming.
    
    Returns:
        UTC timestamp string
    """
    return datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')


if __name__ == "__main__":
    # Test utilities
    print("Testing date utilities...")
    
    test_date = "2026-04-28"
    print(f"\nTest date: {test_date}")
    print(f"Quarter: {get_quarter_from_date(test_date)}")
    print(f"Expiry type: {get_expiry_type(test_date)}")
    print(f"Days to expiry: {get_days_to_expiry(test_date)}")
    print(f"Week label: {format_week_label(test_date)}")
    print(f"Week range: {get_week_range(test_date)}")

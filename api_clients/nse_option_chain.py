"""
NSE Option Chain Live Data Fetcher

Fetches live NIFTY option chain data from NSE India.
Handles session management, cookie handling, and anti-blocking measures.
Provides local caching with TTL for reliability.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import random
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NSEOptionChainClient:
    """
    Client for fetching live NSE NIFTY option chain data.
    
    Features:
    - Proper session and cookie handling
    - Retry logic with exponential backoff
    - Local caching with TTL
    - Graceful fallback to cached data
    - Anti-blocking measures
    """
    
    BASE_URL = "https://www.nseindia.com"
    API_ENDPOINT = f"{BASE_URL}/api/option-chain-indices"
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': f'{BASE_URL}/option-chain',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin'
    }
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize NSE Option Chain client.
        
        Args:
            cache_dir: Directory for caching option chain data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff
        
        # Initialize session cookies
        self._initialize_session()
        
    def _initialize_session(self) -> None:
        """
        Initialize session by visiting NSE homepage to get cookies.
        This is required before making API calls.
        """
        try:
            logger.info("Initializing NSE session...")
            response = self.session.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            logger.info("Session initialized successfully")
            
            # Add small random delay to avoid rate limiting
            time.sleep(random.uniform(0.3, 0.7))
            
        except Exception as e:
            logger.warning(f"Session initialization warning: {e}")
            # Continue anyway - sometimes works without explicit initialization
            
    def get_raw_option_chain(self, symbol: str = "NIFTY") -> Dict[str, Any]:
        """
        Fetch raw option chain JSON from NSE.
        
        Args:
            symbol: Index symbol (default: NIFTY)
            
        Returns:
            Raw JSON response as dictionary
            
        Raises:
            Exception: If all retries fail
        """
        params = {'symbol': symbol}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching option chain (attempt {attempt + 1}/{self.max_retries})...")
                
                response = self.session.get(
                    self.API_ENDPOINT,
                    params=params,
                    timeout=15
                )
                
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response headers: {dict(response.headers)}")
                logger.info(f"Response length: {len(response.content)} bytes")
                
                response.raise_for_status()
                
                # Check if response is JSON
                try:
                    data = response.json()
                except ValueError:
                    logger.error(f"Response is not valid JSON. Content: {response.text[:200]}")
                    raise Exception("Invalid JSON response from NSE")
                
                logger.info(f"Parsed JSON with keys: {list(data.keys())}")
                
                # Check if response is empty or error
                if not data or 'error' in data:
                    error_msg = data.get('error', 'Empty response')
                    logger.warning(f"NSE returned error or empty response: {error_msg}")
                    raise Exception(f"NSE API error: {error_msg}")
                
                logger.info("Successfully fetched option chain data")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delays[attempt]
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
                    # Re-initialize session on failure
                    self._initialize_session()
                else:
                    raise Exception(f"Failed to fetch option chain after {self.max_retries} attempts: {e}")
                    
    def get_expiry_dates(self) -> List[str]:
        """
        Get list of available expiry dates.
        
        Returns:
            Sorted list of expiry dates in DD-MMM-YYYY format
            
        Raises:
            Exception: If unable to fetch data
        """
        try:
            data = self.get_raw_option_chain()
            
            # Debug: Log the structure of the response
            logger.info(f"Response keys: {list(data.keys())}")
            
            if "records" in data:
                logger.info(f"Records keys: {list(data['records'].keys())}")
            
            expiry_dates = data.get("records", {}).get("expiryDates", [])
            
            if not expiry_dates:
                # Try alternative path
                if "records" in data and "data" in data["records"]:
                    # Extract unique expiry dates from data records
                    records = data["records"]["data"]
                    expiry_dates = list(set(record.get("expiryDate", "") for record in records if record.get("expiryDate")))
                    expiry_dates = sorted([d for d in expiry_dates if d])
                    
                if not expiry_dates:
                    logger.error(f"Response structure: {json.dumps(data, indent=2)[:500]}")
                    raise ValueError("No expiry dates found in response")
            
            logger.info(f"Found {len(expiry_dates)} expiry dates")
            return sorted(expiry_dates)
            
        except Exception as e:
            logger.error(f"Error fetching expiry dates: {e}")
            raise
            
    def get_option_chain_by_expiry(self, expiry_date: str) -> pd.DataFrame:
        """
        Fetch option chain for specific expiry date.
        
        Args:
            expiry_date: Expiry date in DD-MMM-YYYY format (e.g., '27-Feb-2026')
            
        Returns:
            DataFrame with option chain data
            
        Raises:
            Exception: If unable to fetch or parse data
        """
        try:
            # Try to fetch live data
            data = self.get_raw_option_chain()
            records = data.get("records", {}).get("data", [])
            spot_price = data.get("records", {}).get("underlyingValue", 0)
            
            if not records:
                raise ValueError("No option chain records found")
                
            # Parse to DataFrame
            df = self.parse_to_dataframe(records, expiry_date, spot_price)
            
            # Save to cache
            self.save_cache(df, expiry_date)
            
            logger.info(f"Successfully parsed {len(df)} option chain rows")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching option chain: {e}")
            
            # Try to load from cache
            logger.info("Attempting to load from cache...")
            cached_df = self.load_cache(expiry_date)
            
            if cached_df is not None:
                logger.info("Using cached data")
                return cached_df
            else:
                raise Exception(f"Failed to fetch live data and no cache available: {e}")
                
    def parse_to_dataframe(self, records: List[Dict], expiry_date: str, spot_price: float) -> pd.DataFrame:
        """
        Parse raw NSE JSON records to standardized DataFrame.
        
        Args:
            records: List of option chain records from NSE
            expiry_date: Expiry date to filter
            spot_price: Current spot price
            
        Returns:
            DataFrame with columns: Strike, Option_Type, Expiry, OI, OI_Change, Volume, IV, Spot_Price
        """
        parsed_data = []
        
        for record in records:
            strike = record.get("strikePrice")
            expiry = record.get("expiryDate")
            
            # Filter by expiry date
            if expiry != expiry_date:
                continue
                
            # Parse CE (Call) data
            if "CE" in record:
                ce_data = record["CE"]
                parsed_data.append({
                    "Strike": strike,
                    "Option_Type": "CE",
                    "Expiry": expiry,
                    "OI": ce_data.get("openInterest", 0),
                    "OI_Change": ce_data.get("changeinOpenInterest", 0),
                    "Volume": ce_data.get("totalTradedVolume", 0),
                    "IV": ce_data.get("impliedVolatility", np.nan),
                    "LTP": ce_data.get("lastPrice", 0),
                    "Bid": ce_data.get("bidprice", 0),
                    "Ask": ce_data.get("askPrice", 0),
                    "Spot_Price": spot_price
                })
                
            # Parse PE (Put) data
            if "PE" in record:
                pe_data = record["PE"]
                parsed_data.append({
                    "Strike": strike,
                    "Option_Type": "PE",
                    "Expiry": expiry,
                    "OI": pe_data.get("openInterest", 0),
                    "OI_Change": pe_data.get("changeinOpenInterest", 0),
                    "Volume": pe_data.get("totalTradedVolume", 0),
                    "IV": pe_data.get("impliedVolatility", np.nan),
                    "LTP": pe_data.get("lastPrice", 0),
                    "Bid": pe_data.get("bidprice", 0),
                    "Ask": pe_data.get("askPrice", 0),
                    "Spot_Price": spot_price
                })
                
        df = pd.DataFrame(parsed_data)
        
        # Ensure numeric types
        numeric_cols = ["Strike", "OI", "OI_Change", "Volume", "IV", "LTP", "Bid", "Ask", "Spot_Price"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Drop rows with zero OI (illiquid strikes)
        df = df[df["OI"] > 0].copy()
        
        # Sort by strike
        df = df.sort_values(["Strike", "Option_Type"]).reset_index(drop=True)
        
        return df
        
    def save_cache(self, df: pd.DataFrame, expiry_date: str) -> None:
        """
        Save DataFrame to local cache.
        
        Args:
            df: DataFrame to cache
            expiry_date: Expiry date for filename
        """
        try:
            # Create filename with date and expiry
            today = datetime.now().strftime("%Y%m%d")
            safe_expiry = expiry_date.replace("-", "").replace(" ", "")
            filename = f"nifty_option_chain_{today}_{safe_expiry}.csv"
            filepath = self.cache_dir / filename
            
            df.to_csv(filepath, index=False)
            logger.info(f"Cached data to {filepath}")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
            
    def load_cache(self, expiry_date: str, ttl_minutes: int = 5) -> Optional[pd.DataFrame]:
        """
        Load data from cache if valid.
        
        Args:
            expiry_date: Expiry date to load
            ttl_minutes: Cache validity in minutes (default: 5)
            
        Returns:
            DataFrame if cache is valid, None otherwise
        """
        try:
            today = datetime.now().strftime("%Y%m%d")
            safe_expiry = expiry_date.replace("-", "").replace(" ", "")
            filename = f"nifty_option_chain_{today}_{safe_expiry}.csv"
            filepath = self.cache_dir / filename
            
            if not filepath.exists():
                logger.info("No cache file found")
                return None
                
            # Check if cache is still valid
            if not self.is_cache_valid(filepath, ttl_minutes):
                logger.info("Cache expired")
                return None
                
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} rows from cache")
            return df
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
            
    def is_cache_valid(self, filepath: Path, ttl_minutes: int) -> bool:
        """
        Check if cache file is still valid.
        
        Args:
            filepath: Path to cache file
            ttl_minutes: Time to live in minutes
            
        Returns:
            True if cache is valid, False otherwise
        """
        try:
            file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
            age = datetime.now() - file_time
            
            is_valid = age < timedelta(minutes=ttl_minutes)
            logger.info(f"Cache age: {age.seconds // 60} minutes, valid: {is_valid}")
            return is_valid
            
        except Exception as e:
            logger.warning(f"Error checking cache validity: {e}")
            return False
            
    def get_spot_price(self) -> float:
        """
        Get current NIFTY spot price.
        
        Returns:
            Current spot price
        """
        try:
            data = self.get_raw_option_chain()
            spot_price = data.get("records", {}).get("underlyingValue", 0)
            logger.info(f"Current NIFTY spot: {spot_price}")
            return spot_price
        except Exception as e:
            logger.error(f"Error fetching spot price: {e}")
            return 0.0

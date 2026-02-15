"""
Configuration loader for the platform.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        # Return default config if file not found
        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return get_default_config()


def get_default_config() -> Dict[str, Any]:
    """Return default configuration if file not available."""
    return {
        'data': {
            'raw_dir': 'data/raw',
            'processed_dir': 'data/processed',
            'reference_dir': 'data/reference'
        },
        'market': {
            'nifty_symbol': '^NSEI',
            'vix_symbol': '^INDIAVIX',
            'atr_period': 14
        },
        'analysis': {
            'pcr_bearish_threshold': 1.3,
            'pcr_bullish_threshold': 0.7,
            'vix_high': 20,
            'vix_low': 11
        },
        'prediction': {
            'weights': {
                'statistical': 0.4,
                'rule_based': 0.3,
                'iv_based': 0.3
            }
        }
    }


def get_data_paths(config: Dict = None) -> Dict[str, Path]:
    """
    Get data paths from config.
    
    Args:
        config: Configuration dict (loads from file if None)
        
    Returns:
        Dictionary of Path objects
    """
    if config is None:
        config = load_config()
    
    data_config = config.get('data', {})
    
    return {
        'raw': Path(data_config.get('raw_dir', 'data/raw')),
        'processed': Path(data_config.get('processed_dir', 'data/processed')),
        'reference': Path(data_config.get('reference_dir', 'data/reference')),
        'daily': Path(data_config.get('daily_dir', 'data/raw/daily')),
        'weekly': Path(data_config.get('weekly_dir', 'data/raw/weekly')),
        'monthly': Path(data_config.get('monthly_dir', 'data/raw/monthly'))
    }


def get_thresholds(config: Dict = None) -> Dict[str, Any]:
    """
    Get analysis thresholds from config.
    
    Args:
        config: Configuration dict
        
    Returns:
        Thresholds dictionary
    """
    if config is None:
        config = load_config()
    
    analysis = config.get('analysis', {})
    rules = config.get('rules', {})
    
    return {
        'pcr_bullish': analysis.get('pcr_bullish_threshold', 0.7),
        'pcr_bearish': analysis.get('pcr_bearish_threshold', 1.3),
        'vix_low': analysis.get('vix_low', 11),
        'vix_high': analysis.get('vix_high', 20),
        'concentration': analysis.get('concentration_threshold', 50),
        'rules': rules
    }


if __name__ == "__main__":
    # Test config loading
    config = load_config()
    
    print("Configuration loaded successfully!")
    print(f"\nData paths:")
    paths = get_data_paths(config)
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    print(f"\nThresholds:")
    thresholds = get_thresholds(config)
    for key, value in thresholds.items():
        if key != 'rules':
            print(f"  {key}: {value}")

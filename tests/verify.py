#!/usr/bin/env python3
"""Quick verification script."""

import sys
from pathlib import Path

# Add parent directory (project root) to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print('=' * 70)
print('FINAL PLATFORM VERIFICATION')
print('=' * 70)

modules_to_check = [
    ('utils.config_loader', 'Config Loader'),
    ('data_loader', 'Data Loader'),
    ('utils.date_utils', 'Date Utils'),
    ('utils.assertion_rules', 'Assertion Rules'),
    ('metrics', 'Metrics Engine'),
    ('insights', 'Insights Engine'),
    ('visualization', 'Visualization Engine'),
    ('analysis.comparisons', 'Comparison Engine'),
    ('analysis.range_predictor', 'Range Predictor'),
    ('analysis.strategy_builder', 'Strategy Builder'),
    ('api_clients.market_data', 'Market Data Client'),
    ('api_clients.nse_option_chain', 'NSE Option Chain Client'),
]

passed = 0
failed = 0

for module_name, display_name in modules_to_check:
    try:
        __import__(module_name)
        print(f'✅ {display_name:25} ({module_name})')
        passed += 1
    except Exception as e:
        print(f'❌ {display_name:25} Error: {str(e)[:50]}')
        failed += 1

print('=' * 70)
print(f'RESULT: {passed}/{len(modules_to_check)} modules verified')
if passed == len(modules_to_check):
    print('STATUS: ALL COMPONENTS COMPLETE ✅')
print('=' * 70)

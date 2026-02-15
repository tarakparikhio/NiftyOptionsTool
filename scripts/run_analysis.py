"""
Main Analysis Runner

Orchestrates the complete analysis pipeline:
1. Load data
2. Run comparisons
3. Generate range predictions
4. Apply assertion rules
5. Generate reports
"""

import pandas as pd
import sys
from pathlib import Path
import argparse
from datetime import datetime
import json

# Add project root to path (parent directory of scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_loader import OptionsDataLoader
from api_clients.market_data import MarketDataClient
from metrics import OptionsMetrics
from analysis.comparisons import ComparisonEngine
from analysis.range_predictor import RangePredictor
from insights import InsightsEngine


def run_full_analysis(data_path: str = "data/raw/monthly", 
                      output_dir: str = "output"):
    """
    Run complete analysis pipeline.
    
    Args:
        data_path: Path to options data
        output_dir: Directory for saving outputs
    """
    print("\n" + "="*70)
    print("NIFTY OPTIONS RESEARCH PLATFORM - FULL ANALYSIS")
    print("="*70)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime now().strftime('%Y%m%d_%H%M%S')
    
    # ========== 1. LOAD DATA ==========
    print("\n[1/6] Loading Options Data...")
    loader = OptionsDataLoader(data_path)
    weekly_data = loader.load_all_weeks()
    
    if not weekly_data:
        print("❌ No data found!")
        return
    
    print(f"✓ Loaded {len(weekly_data)} weeks: {loader.weeks}")
    
    # Add derived columns
    for week in weekly_data:
        weekly_data[week] = loader.add_derived_columns(weekly_data[week])
    
    latest_week = loader.get_latest_week()
    current_df = weekly_data[latest_week]
    
    # ========== 2. FETCH LIVE DATA ==========
    print("\n[2/6] Fetching Live Market Data...")
    client = MarketDataClient()
    
    nifty_data = client.fetch_nifty()
    vix_data = client.fetch_vix()
    nifty_hist = client.get_historical_nifty(days=30)
    
    current_spot = nifty_data.get('close', current_df['Spot_Price'].iloc[0] if not current_df.empty else 26000)
    current_vix = vix_data.get('vix_value', 15.0)
    
    print(f"✓ Nifty: {current_spot:.2f}")
    print(f"✓ VIX: {current_vix:.2f}")
    
    # ========== 3. COMPUTE METRICS ==========
    print("\n[3/6] Computing Positioning Metrics...")
    metrics = OptionsMetrics(current_df)
    
    pcr_df = metrics.compute_pcr(by_expiry=False)
    pcr = pcr_df['PCR'].iloc[0] if not pcr_df.empty else 0
    
    max_pain = metrics.compute_max_pain()
    concentration = metrics.compute_oi_concentration()
    top_strikes = metrics.get_top_oi_strikes(n=5)
    
    print(f"✓ PCR: {pcr:.2f}")
    print(f"✓ Max Pain: {max_pain:.0f}")
    print(f"✓ OI Concentration: {concentration['concentration_ratio']:.1f}%")
    
    # ========== 4. HISTORICAL COMPARISON ==========
    print("\n[4/6] Running Historical Comparisons...")
    comp_engine = ComparisonEngine(weekly_data)
    
    comparison_summary = comp_engine.get_comparison_summary(latest_week)
    migration = comp_engine.detect_strike_migration_pattern()
    
    print(f"✓ CE Strike Migration: {migration['ce_trend']}")
    print(f"✓ PE Strike Migration: {migration['pe_trend']}")
    
    # ========== 5. RANGE PREDICTION ==========
    print("\n[5/6] Predicting Next-Day Range...")
    predictor = RangePredictor(
        options_data=current_df,
        historical_nifty=nifty_hist,
        current_vix=current_vix,
        current_spot=current_spot
    )
    
    ensemble_pred = predictor.predict_ensemble()
    levels = predictor.predict_intraday_levels()
    
    print(f"✓ Predicted Range: {ensemble_pred['lower_range']:.0f} - {ensemble_pred['upper_range']:.0f}")
    print(f"✓ Confidence: {ensemble_pred['confidence']:.1f}%")
    
    # ========== 6. GENERATE INSIGHTS ==========
    print("\n[6/6] Generating Insights...")
    insights_engine = InsightsEngine(weekly_data, latest_week)
    insights = insights_engine.generate_all_insights()
    insights_summary = insights_engine.generate_summary()
    
    print(f"✓ Generated {len(insights)} insights")
    
    # ========== SAVE OUTPUTS ==========
    print("\n[SAVING] Writing output files...")
    
    # Save JSON summary
    output_data = {
        'timestamp': datetime.now().isoformat(),
        'analysis_date': latest_week,
        'market_data': {
            'nifty_spot': float(current_spot),
            'vix': float(current_vix)
        },
        'metrics': {
            'pcr': float(pcr),
            'max_pain': float(max_pain),
            'oi_concentration': float(concentration['concentration_ratio'])
        },
        'range_prediction': {
            'method': ensemble_pred['method'],
            'lower_range': float(ensemble_pred['lower_range']),
            'upper_range': float(ensemble_pred['upper_range']),
            'expected_up_move': float(ensemble_pred['expected_up_move']),
            'expected_down_move': float(ensemble_pred['expected_down_move']),
            'confidence': float(ensemble_pred['confidence'])
        },
        'migration': {
            'ce_trend': migration['ce_trend'],
            'pe_trend': migration['pe_trend']
        },
        'insights_count': len(insights),
        'bullish_signals': sum(1 for i in insights if i['signal'] == 'BULLISH'),
        'bearish_signals': sum(1 for i in insights if i['signal'] == 'BEARISH')
    }
    
    json_file = output_path / f'analysis_summary_{timestamp}.json'
    with open(json_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"✓ Saved JSON: {json_file}")
    
    # Save detailed report
    report_file = output_path / f'analysis_report_{timestamp}.txt'
    with open(report_file, 'w') as f:
        f.write(insights_summary)
        f.write("\n\n")
        f.write(predictor.get_prediction_report())
    
    print(f"✓ Saved Report: {report_file}")
    
    # Save CSV exports
    top_strikes.to_csv(output_path / f'top_strikes_{timestamp}.csv', index=False)
    
    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE!")
    print("="*70)
    
    # Print quick summary
    print("\n📊 QUICK SUMMARY:")
    print(f"  Current Spot: {current_spot:,.0f}")
    print(f"  VIX: {current_vix:.2f}")
    print(f"  PCR: {pcr:.2f}")
    print(f"  Predicted Range: {ensemble_pred['lower_range']:,.0f} - {ensemble_pred['upper_range']:,.0f}")
    print(f"  Confidence: {ensemble_pred['confidence']:.1f}%")
    print(f"  Strike Migration: CE {migration['ce_trend']}, PE {migration['pe_trend']}")
    print(f"\n📁 Outputs saved to: {output_path}\n")
    
    return output_data


def quick_range_check():
    """Quick range prediction without full analysis."""
    print("\n🚀 QUICK RANGE PREDICTION")
    print("="*50)
    
    loader = OptionsDataLoader("data/raw/monthly")
    weekly_data = loader.load_all_weeks()
    
    if not weekly_data:
        print("No data found!")
        return
    
    latest_week = loader.get_latest_week()
    current_df = loader.get_data_for_week(latest_week)
    
    client = MarketDataClient()
    nifty_hist = client.get_historical_nifty(days=30)
    vix_data = client.fetch_vix()
    
    current_spot = current_df['Spot_Price'].iloc[0] if not current_df.empty else 26000
    current_vix = vix_data.get('vix_value', 15.0)
    
    predictor = RangePredictor(
        options_data=current_df,
        historical_nifty=nifty_hist,
        current_vix=current_vix,
        current_spot=current_spot
    )
    
    print(predictor.get_prediction_report())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Nifty Options Research Platform')
    parser.add_argument('--mode', choices=['full', 'quick'], default='full',
                       help='Analysis mode: full or quick range check')
    parser.add_argument('--data-path', default='data/raw/monthly',
                       help='Path to options data')
    parser.add_argument('--output-dir', default='output',
                       help='Output directory')
    
    args = parser.parse_args()
    
    if args.mode == 'quick':
        quick_range_check()
    else:
        run_full_analysis(args.data_path, args.output_dir)

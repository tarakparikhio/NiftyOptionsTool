"""
Integration Guide: Directional Trading Engine

⚠️ NOTE: This workflow example uses the legacy strategy_builder API
   (archived in archive/legacy_v1.0/strategy_builder_old.py)
   
   For new code, see analysis/strategy_builder.py (V2) which provides:
   - Strategy class with comprehensive risk metrics
   - create_iron_condor(), create_strangle(), create_straddle() functions
   - Professional UI components (analysis/strategy_ui.py)

This module demonstrates how to use the updated components:
1. Directional Signal Engine (RSI + PCR)
2. Strategy Builder (with premium handling)
3. Position Sizer (with Kelly sample adjustment)
4. Risk Engine (fat-tail aware)
5. Decision Engine (signal integration)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

# Import all updated components
from analysis.directional_signal import DirectionalSignalEngine, DirectionalSignal
# NOTE: Importing from archived legacy version for this example
import sys
sys.path.append('archive/legacy_v1.0')
from strategy_builder_old import StrategyTemplate, IronCondor, Strangle
sys.path.remove('archive/legacy_v1.0')
from analysis.position_sizer import PositionSizer
from analysis.range_predictor import RangePredictor
from analysis.decision_engine import DecisionEngine
from analysis.risk_engine import RiskEngine


class DirectionalTradingWorkflow:
    """
    End-to-end workflow for directional trading decisions.
    """
    
    def __init__(self, account_size: float = 100000.0):
        """
        Initialize trading workflow.
        
        Args:
            account_size: Total account capital
        """
        self.account_size = account_size
        
        # Initialize all components
        self.signal_engine = DirectionalSignalEngine(
            rsi_oversold=30,
            rsi_overbought=70,
            pcr_oversold=0.7,
            pcr_overbought=1.3
        )
        
        self.position_sizer = PositionSizer(
            account_size=account_size,
            max_risk_pct=2.0,  # 2% max per trade
            lot_size=50
        )
        
        self.decision_engine = DecisionEngine(config={
            'vol_edge_threshold': 0.15,
            'min_trade_score': 60,
            'min_risk_reward': 1.5,
            'max_risk_of_ruin': 0.20
        })
        
        self.risk_model = RiskEngine()
    
    def execute_full_workflow(
        self,
        price_history: pd.Series,  # 1H closes
        option_chain_df: pd.DataFrame,  # Current options data
        historical_nifty: pd.DataFrame,  # OHLC for range prediction
        current_vix: float,
        current_spot: float,
        trade_history: pd.DataFrame = None  # Past trades for Kelly calc
    ) -> Dict[str, Any]:
        """
        Execute complete trading workflow.
        
        Returns:
            Structured decision object
        """
        
        # STEP 1: Generate directional signal
        print("="*60)
        print("STEP 1: Directional Signal Generation")
        print("="*60)
        
        signal = self.signal_engine.generate_signal(
            price_series=price_history,
            option_df=option_chain_df
        )
        
        print(self.signal_engine.get_signal_summary(signal))
        print()
        
        # STEP 2: Predict range (with fat-tail adjustment)
        print("="*60)
        print("STEP 2: Price Range Prediction")
        print("="*60)
        
        range_predictor = RangePredictor(
            options_data=option_chain_df,
            historical_nifty=historical_nifty,
            current_vix=current_vix,
            current_spot=current_spot
        )
        
        range_pred = range_predictor.predict_statistical()
        print(f"Statistical Range: {range_pred['lower_range']:.0f} - {range_pred['upper_range']:.0f}")
        if 'fat_tail_lower' in range_pred:
            print(f"Fat-tail Range:    {range_pred['fat_tail_lower']:.0f} - {range_pred['fat_tail_upper']:.0f}")
        print(f"Expected Move:     {range_pred['expected_move']:.0f} points")
        print(f"Fat-tail Multiplier: {range_pred.get('fat_tail_multiplier', 1.0):.2f}x")
        print()
        
        # STEP 3: Choose strategy based on signal
        print("="*60)
        print("STEP 3: Strategy Selection")
        print("="*60)
        
        if signal.signal == "CALL_BUY":
            print("🎯 Directional Signal: CALL BUY")
            strategy = self._build_call_strategy(
                spot=current_spot,
                range_pred=range_pred
            )
            strategy_type = "LONG_CALL"
        elif signal.signal == "PUT_BUY":
            print("🎯 Directional Signal: PUT BUY")
            strategy = self._build_put_strategy(
                spot=current_spot,
                range_pred=range_pred
            )
            strategy_type = "LONG_PUT"
        else:
            print("🔕 No directional signal - considering neutral strategies")
            strategy = None
            strategy_type = None
        
        if strategy:
            print(f"Strategy: {strategy['name']}")
            print(f"  Max Profit: ₹{strategy['max_profit']:.0f}")
            print(f"  Max Loss: ₹{strategy['max_loss']:.0f}")
            print(f"  RR Ratio: {strategy['rr_ratio']:.2f}")
            print()
        
        # STEP 4: Volatility edge analysis
        print("="*60)
        print("STEP 4: Volatility Edge Analysis")
        print("="*60)
        
        vol_edge = self.decision_engine.compute_vol_edge(
            option_df=option_chain_df,
            historical_df=historical_nifty,
            spot_price=current_spot
        )
        
        print(f"ATM IV: {vol_edge.get('atm_iv', 0):.2%}")
        print(f"Realized Vol: {vol_edge.get('realized_vol', 0):.2%}")
        print(f"Vol Edge Score: {vol_edge['vol_edge_score']:+.3f}")
        print(f"Interpretation: {vol_edge['interpretation']}")
        print()
        
        # STEP 5: Position sizing with Kelly adjustment
        print("="*60)
        print("STEP 5: Position Sizing (Kelly Adjusted)")
        print("="*60)
        
        # Calculate sample size from trade history
        sample_size = len(trade_history) if trade_history is not None else 0
        win_rate = 0.55  # Example: 55% win rate
        avg_rr = 2.0     # Example: 2:1 risk-reward
        
        kelly_result = self.position_sizer.kelly_fraction(
            win_rate=win_rate,
            avg_rr=avg_rr,
            sample_size=sample_size,
            safety_factor=0.25
        )
        
        print(f"Win Rate: {win_rate:.1%}")
        print(f"Avg R:R Ratio: {avg_rr:.2f}")
        print(f"Sample Size: {sample_size} trades")
        print(f"Uncertainty Factor: {kelly_result['uncertainty_factor']:.2f}x")
        print(f"Recommended Risk: {kelly_result['recommended_fraction']:.2%} of account")
        print(f"Capital at Risk: ₹{kelly_result['capital_at_risk']:.0f}")
        
        if kelly_result['warnings']:
            print("⚠️ Warnings:")
            for warn in kelly_result['warnings']:
                print(f"   {warn}")
        print()
        
        # STEP 6: Risk simulation
        print("="*60)
        print("STEP 6: Risk Simulation (10,000 paths)")
        print("="*60)
        
        risk_metrics = self.risk_model.simulate_equity_paths(
            starting_capital=self.account_size,
            win_rate=win_rate,
            avg_rr=avg_rr,
            risk_per_trade=kelly_result['recommended_fraction'],
            num_simulations=10000,
            num_trades=30
        )
        
        print(f"Final Equity Range:")
        print(f"  5th percentile (bad): ₹{risk_metrics['percentiles']['5']:.0f}")
        print(f"  50th percentile (median): ₹{risk_metrics['percentiles']['50']:.0f}")
        print(f"  95th percentile (good): ₹{risk_metrics['percentiles']['95']:.0f}")
        print(f"Max Drawdown: {risk_metrics['max_drawdown_pct']:.1f}%")
        print(f"Risk of Ruin: {risk_metrics['risk_of_ruin']:.1%}")
        print()
        
        # STEP 7: Final decision validation
        print("="*60)
        print("STEP 7: Final Decision Validation")
        print("="*60)
        
        if strategy_type:
            validation = self.decision_engine.validate_with_directional_signal(
                directional_signal=signal,
                strategy_type=strategy_type,
                vol_edge_score=vol_edge['vol_edge_score'],
                risk_of_ruin=risk_metrics['risk_of_ruin']
            )
            
            print(f"Decision: {'✅ TRADE' if validation['allowed'] else '❌ DO NOT TRADE'}")
            print(f"Confidence: {validation['confidence']}/100")
            print()
            
            print("Reasons:")
            for reason in validation['reasons']:
                print(f"  {reason}")
            
            if validation['warnings']:
                print("\n⚠️ Warnings:")
                for warn in validation['warnings']:
                    print(f"  {warn}")
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        
        return {
            'signal': signal,
            'range_prediction': range_pred,
            'strategy': strategy,
            'vol_edge': vol_edge,
            'kelly_sizing': kelly_result,
            'risk_metrics': risk_metrics,
            'validation': validation if strategy_type else None
        }
    
    def _build_call_strategy(
        self,
        spot: float,
        range_pred: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build long call strategy for bullish signal.
        """
        # Select strike: slightly ATM or 1-2 steps OTM
        # For NIFTY, steps are usually 100 points
        call_strike = round(spot + 100, -2)  # 1 step OTM
        
        # Create strategy
        strategy = StrategyTemplate("Long Call", spot, dte=7)
        strategy.add_leg('CE', call_strike, 'buy', quantity=1)
        
        # Payoff with premium (example: paid ₹150 for the call)
        entry_premiums = {('CE', call_strike, 'buy'): 150}
        spot_range = np.linspace(spot * 0.95, spot * 1.05, 100)
        payoff = strategy.compute_payoff(spot_range, entry_premiums=entry_premiums)
        
        return {
            'name': 'Long Call',
            'strike': call_strike,
            'max_profit': np.max(payoff),
            'max_loss': abs(np.min(payoff)),
            'rr_ratio': np.max(payoff) / abs(np.min(payoff)) if np.min(payoff) != 0 else 0
        }
    
    def _build_put_strategy(
        self,
        spot: float,
        range_pred: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build long put strategy for bearish signal.
        """
        # Select strike: slightly ATM or 1-2 steps OTM
        put_strike = round(spot - 100, -2)  # 1 step OTM
        
        # Create strategy
        strategy = StrategyTemplate("Long Put", spot, dte=7)
        strategy.add_leg('PE', put_strike, 'buy', quantity=1)
        
        # Payoff with premium (example: paid ₹150 for the put)
        entry_premiums = {('PE', put_strike, 'buy'): 150}
        spot_range = np.linspace(spot * 0.95, spot * 1.05, 100)
        payoff = strategy.compute_payoff(spot_range, entry_premiums=entry_premiums)
        
        return {
            'name': 'Long Put',
            'strike': put_strike,
            'max_profit': np.max(payoff),
            'max_loss': abs(np.min(payoff)),
            'rr_ratio': np.max(payoff) / abs(np.min(payoff)) if np.min(payoff) != 0 else 0
        }


# Example usage (pseudocode, real data would come from your CSV)
if __name__ == "__main__":
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     DIRECTIONAL TRADING ENGINE - COMPLETE WORKFLOW        ║
    ║                                                            ║
    ║  This integration demonstrates:                           ║
    ║  1️⃣  RSI + PCR directional signals                         ║
    ║  2️⃣  Strategy payoff with premium handling                 ║
    ║  3️⃣  Conservative Kelly sizing                             ║
    ║  4️⃣  Fat-tail aware range prediction                       ║
    ║  5️⃣  Risk simulation (10,000 paths)                        ║
    ║  6️⃣  Signal-driven decision validation                     ║
    ║                                                            ║
    ║  All components now work together seamlessly.             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    print("""
    📋 TO RUN FULL WORKFLOW:
    
    1. Load your data:
       - price_history = pd.read_csv("prices_1h.csv")
       - option_chain = pd.read_csv("options.csv")
       - nifty_history = pd.read_csv("nifty_ohlc.csv")
    
    2. Create workflow:
       workflow = DirectionalTradingWorkflow(account_size=100000)
    
    3. Execute:
       result = workflow.execute_full_workflow(
           price_history=price_history['close'],
           option_chain_df=option_chain,
           historical_nifty=nifty_history,
           current_vix=20.5,
           current_spot=23450
       )
    
    4. Access results:
       result['signal']           # Directional signal
       result['validation']       # Trade allowed?
       result['kelly_sizing']     # Position size
       result['risk_metrics']     # Risk of ruin
    """)

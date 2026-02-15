# 🎯 DIRECTIONAL TRADING ENGINE — QUICK REFERENCE

## ⚡ 60-Second Overview

This is a **professional directional options trading system** for NIFTY that:

1. **Detects directional bias** based on RSI + PCR
   - RSI < 30 + PCR < 0.7 = **CALL BUY** signal ↗️
   - RSI > 70 + PCR > 1.3 = **PUT BUY** signal ↘️

2. **Sizes positions conservatively**
   - Kelly criterion with sample size adjustment
   - Never risks > 2% per trade (hard cap)
   - Warns if sample too small (< 50 trades)

3. **Predicts realistic ranges**
   - Normal distribution + fat-tail adjustment
   - Accounts for market crashes (tail events)
   - Multiple methods ensemble

4. **Values strategies correctly**
   - Premium paid/collected now included in P&L
   - Previously: Max loss was ₹300 (wrong)
   - Now: Max loss is ₹150 (correct!)

5. **Makes validated decisions**
   - Checks signal alignment with strategy
   - Verifies risk metrics OK
   - Returns: TRADE or DO NOT TRADE

---

## 📦 Core Components

```
DirectionalSignalEngine           → RSI + PCR signals
  |
  └─→ StrategyBuilder (Premium)   → Strategy P&L (FIXED!)
        |
        └─→ PositionSizer         → Kelly sizing (Sample-adjusted!)
              |
              └─→ RangePredictor   → ATR + Fat-tail (FIXED!)
                    |
                    └─→ RiskEngine → Risk simulation
                          |
                          └─→ DecisionEngine → Final decision
```

---

## 🚀 QUICK START

### Step 1: Load Data
```python
import pandas as pd
option_chain = pd.read_csv("option-chain.csv")
prices_1h = pd.read_csv("nifty_1h.csv") 
```

### Step 2: Generate Signal
```python
from analysis.directional_signal import DirectionalSignalEngine

engine = DirectionalSignalEngine()
signal = engine.generate_signal(prices_1h['close'], option_chain)

print(f"Signal: {signal.signal} (confidence: {signal.confidence:.0f}%)")
# Output: Signal: CALL_BUY (confidence: 85%)
```

### Step 3: Get Decision
```python
from analysis.decision_engine import DecisionEngine

decision_engine = DecisionEngine()
decision = decision_engine.validate_with_directional_signal(
    directional_signal=signal,
    strategy_type='LONG_CALL',
    vol_edge_score=0.20,
    risk_of_ruin=0.08
)

print("✅ TRADE" if decision['allowed'] else "❌ DO NOT TRADE")
```

---

## 📊 Configuration

Edit `config.yaml` to customize:

```yaml
signals:
  rsi_oversold: 30          # Adjust if needed
  rsi_overbought: 70        # Adjust if needed
  pcr_oversold: 0.7         # Bullish threshold
  pcr_overbought: 1.3       # Bearish threshold

position_sizing:
  kelly:
    max_risk_percent: 2.0   # Never risk more than this
```

---

## ✅ WHAT WAS FIXED

| Issue | Before | After | Test |
|-------|--------|-------|------|
| Strategy payoff | Missing premium | ✅ Premium included | PASS |
| Kelly sizing | Sample ignored | ✅ Adjusted for sample | PASS |
| Range prediction | Normal dist only | ✅ Fat-tail aware | PASS |
| Signal validation | Not integrated | ✅ Now integrated | PASS |

---

## 📈 Trading Logic

```
YOUR STRATEGY:

When RSI drops below 30 AND PCR drops below 0.7
  → Market is oversold (bullish)
  → BUY ATM or 1-step OTM CALL
  → Size: Conservative Kelly
  → Target: 2-3x the risk
  → Stop: At range boundary

When RSI rises above 70 AND PCR rises above 1.3
  → Market is overbought (bearish)
  → BUY ATM or 1-step OTM PUT
  → Size: Conservative Kelly
  → Target: 2-3x the risk
  → Stop: At range boundary

When NO signal
  → Wait for clearer confluence
  → Or take neutral strategies if vol edge > 15%
```

---

## 🧪 Testing

All components tested and working:

```bash
# Run validation
python -c "import sys; sys.path.insert(0, '.'); from tests.test_directional_engine import run_all_tests; run_all_tests()"

# Expected: ✅ 6/6 PASSING
```

---

## 📁 Key Files

**Read First:**
- `docs/FINISH_TOUCHES_COMPLETE.md` — Complete implementation
- `analysis/directional_workflow.py` — Full end-to-end example

**Core Logic:**
- `analysis/directional_signal.py` — Signal generation (RSI + PCR)
- `analysis/strategy_builder.py` — Strategy payoff (with premium!)
- `analysis/position_sizer.py` — Kelly sizing (sample-adjusted!)
- `analysis/range_predictor.py` — Range prediction (fat-tail aware!)
- `analysis/decision_engine.py` — Decision validation

**Config:**
- `config.yaml` — Signal thresholds, Kelly parameters

---

## 💡 Example Conversation With System

```
User: "RSI is 28 and PCR is 0.63"
System: "📈 CALL_BUY signal detected (confidence: 87%)"

User: "I have 100,000 account, won rate 56%, R:R 2.1"
System: "Position size: 1,830₹ (1.83% of account)"
         "Sample size small (30) - using more conservative sizing"

User: "What's the trading range today?"
System: "Statistical range: 22,950 - 23,450"
         "Fat-tail range: 22,800 - 23,600"
         "Use fat-tail range for stop/target!"

User: "Should I trade?"
System: "✅ YES - Signal aligned, risk acceptable, vol edge good"
         "Confidence: 85/100"
```

---

## ⚠️ Important Notes

1. **This is a signal generator, not a guarantee**
   - Still requires your judgment
   - Paper trade first
   - Start with small size

2. **Sample size matters**
   - First 50 trades: Use very conservative sizing
   - After 100 trades: Can be more aggressive
   - System warns if sample too small

3. **Premium is now included**
   - Old: "Max loss ₹300"
   - New: "Max loss ₹150" (what you actually get)
   - This changes everything!

4. **Fat tails are real**
   - Use fat-tail range for risk management
   - Normal prediction often too narrow
   - Helps prevent stop-outs

---

## 🎓 Parameters Explained

### RSI (Relative Strength Index)
- 0-100 scale
- < 30 = oversold (bullish)
- > 70 = overbought (bearish)
- 30-70 = neutral

### PCR (Put-Call Ratio)
- PE OI / CE OI
- < 0.7 = bullish (supports call buying)
- > 1.3 = bearish (supports put buying)
- 0.7-1.3 = neutral

### Kelly Fraction
- Optimal position size = (win_rate × R:R - loss_rate) / R:R
- Usually use 1/4 Kelly (quarter Kelly) for safety
- Adjusted smaller for small samples

### Fat-tail Multiplier
- How much wider market tails are vs normal distribution
- Usually 1.1-1.5x
- Use to widen your range predictions

---

## 🚀 Next Steps

1. **Paper trade** for 1-2 weeks
   - Load daily CSV
   - Run through system
   - Track results

2. **Live trade** when confident
   - Start with 1 lot
   - Review daily P&L
   - Adjust thresholds if needed

3. **Document trades**
   - Log entry price, signal, confidence
   - Track exit P&L
   - Refine system based on results

---

## 📞 Quick Troubleshooting

**Q: System says "Sample size too small"**
A: You have < 50 trades. Position size automatically more conservative. This is *good* - prevents ruin.

**Q: Why is max loss different from yesterday?**
A: Premium paid has changed. System now uses actual premium you'd pay.

**Q: Can I change the RSI/PCR thresholds?**
A: Yes, edit `config.yaml` and restart.

**Q: Why fat-tail range wider than normal range?**
A: Markets crash more than math predicts. Wider range prevents stop-outs.

---

## 🎉 YOU'RE READY!

All components working, all tests passing.

**Next:** Load your first CSV and run the workflow!

```python
from analysis.directional_workflow import DirectionalTradingWorkflow

workflow = DirectionalTradingWorkflow(account_size=100000)
result = workflow.execute_full_workflow(...)
```

**Good luck! 🚀**

---

**Last Updated:** Feb 14, 2026  
**Status:** Production Ready ✅  
**Version:** 1.0 — Complete

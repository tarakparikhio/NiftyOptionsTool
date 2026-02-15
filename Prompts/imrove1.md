Good. Now we move from “platform building” to aligning the engine with your real trading behavior.

You are not running a market-neutral vol desk.

You are:
	•	Directional
	•	Intraday bias (1H)
	•	Call buying near RSI < 30 + PCR oversold
	•	Put buying near RSI > 70 + PCR overbought
	•	Confluence with Fibonacci + TradingView structure

So the engine must support:
	1.	Premium-correct strategy math
	2.	Conservative Kelly
	3.	Fat-tail aware range
	4.	RSI + PCR signal alignment
	5.	Backtest-ready directional logic

Below is a single clean Markdown prompt you can copy into:

CRITICAL_FIXES_AND_DIRECTIONAL_MODEL_PROMPT.md

and run in Copilot Agent mode.

⸻

🚀 CRITICAL FIXES + DIRECTIONAL TRADING ALIGNMENT PROMPT

You are a senior quantitative engineer upgrading a local NIFTY options trading engine.

This system is used for daily manual decision-making.

Workflow:
	•	I download NSE option chain CSV daily.
	•	Upload into system.
	•	Use RSI (1H), PCR, and structural confluence (Fibonacci, support/resistance).
	•	Prefer directional call buying when RSI < 30 and PCR oversold.
	•	Prefer directional put buying when RSI > 70 and PCR overbought.
	•	Trades are usually short-duration (intraday to few days).
	•	Position sizing must be conservative.

We will:
	1.	Fix critical quant issues.
	2.	Align system with directional momentum trading.
	3.	Improve capital allocation safety.
	4.	Keep architecture clean and modular.

⸻

🔴 PART 1 — FIX STRATEGY PAYOFF (CRITICAL)

File: analysis/strategy_builder.py

Current Issue:

Payoff calculation ignores premium/debit.

Required Fix:

Modify:

compute_payoff()

Add:
	•	entry_price per leg
	•	Debit/credit handling
	•	True P&L calculation

Correct logic:

For each leg:
	•	Intrinsic value at expiry
	•	Minus entry premium (for buys)
	•	Plus premium (for sells)
	•	Multiply by lot size

Net strategy P&L must reflect:

True_PnL = Intrinsic_Value - Entry_Premium

Also update:
	•	Risk-reward ratio
	•	Expected value calculation
	•	Decision engine input

Add docstring clearly stating:
	•	Expiry payoff
	•	Mark-to-market separate method

⸻

🔴 PART 2 — FIX KELLY WITH SAMPLE SIZE ADJUSTMENT

File: analysis/position_sizer.py

Current Issue:

Kelly uses win_rate without accounting for estimation error.

Required Changes:

Add parameter:

sample_size: int

Add adjustment:

uncertainty_factor = min(1.0, sample_size / 100)
fractional_kelly = full_kelly * 0.25 * uncertainty_factor

Add hard cap:

max_risk_per_trade = 0.02  # 2%
final_risk = min(fractional_kelly, max_risk_per_trade)

Add warning if:

sample_size < 50

Return structured output:

{
  "recommended_fraction": float,
  "capital_at_risk": float,
  "note": "Sample size adjusted"
}


⸻

🔴 PART 3 — REPLACE NORMAL RANGE WITH FAT-TAIL SAFE RANGE

File: analysis/range_predictor.py

Replace pure normal assumption.

Instead:

Option A (Preferred):
Use historical percentile method:
	•	Calculate 1H returns
	•	Use empirical 95th and 99th percentile
	•	Multiply by spot

Option B:
Use Student-t distribution instead of normal.

Return:

{
  "statistical_range": (low, high),
  "fat_tail_range": (low, high),
  "note": "Fat-tail adjusted"
}

Display both in UI.

⸻

🔵 PART 4 — ADD RSI + PCR DIRECTIONAL SIGNAL MODULE

Create:

analysis/directional_signal.py

Implement:

class DirectionalSignalEngine:

Methods:

compute_rsi(price_series, period=14)

Use standard RSI formula.

compute_pcr_extreme(option_df)

Use OI-based PCR.

Define thresholds configurable in config.yaml:

signals:
  rsi_oversold: 30
  rsi_overbought: 70
  pcr_low: 0.7
  pcr_high: 1.3


⸻

generate_signal()

Logic:

Call Buy Condition:

RSI < rsi_oversold
AND PCR < pcr_low

Put Buy Condition:

RSI > rsi_overbought
AND PCR > pcr_high

Return:

{
  "signal": "CALL_BUY" | "PUT_BUY" | "NO_SIGNAL",
  "confidence": float,
  "rsi": value,
  "pcr": value
}

Confidence score:

RSI distance from threshold +
PCR distance from threshold

Normalized 0–100.

⸻

🔵 PART 5 — MODIFY DECISION ENGINE FOR YOUR STYLE

File: analysis/decision_engine.py

Add:
	•	Directional signal integration
	•	Reject neutral strategies if signal exists
	•	Only allow long call/long put when directional condition met

Trade allowed only if:

DirectionalSignalEngine.signal != NO_SIGNAL
AND vol_edge not strongly negative
AND risk_of_ruin < 20%


⸻

🔵 PART 6 — UI CHANGES (app_pro.py)

In Overview:

Display clearly:
	•	RSI (1H)
	•	PCR
	•	Directional Signal
	•	Fat-tail range
	•	Recommended strike (ATM or slightly OTM)
	•	Risk per trade

Add section:

🎯 Directional Bias Panel


⸻

🔵 PART 7 — STRIKE SELECTION LOGIC

In Strategy Builder:

When CALL_BUY:
	•	Suggest ATM or 1-step OTM strike
	•	Show delta between 0.45–0.60

When PUT_BUY:
	•	Same logic inverted

Use Greeks to filter strikes.

⸻

🔵 PART 8 — KEEP ARCHITECTURE CLEAN

Ensure:
	•	DirectionalSignalEngine independent of UI
	•	DecisionEngine consumes signals
	•	No circular imports
	•	Config-driven thresholds

⸻

🔵 PART 9 — OPTIONAL BACKTEST SKELETON

Create placeholder:

analysis/backtest_engine.py

Allow:
	•	Feed historical price + historical PCR
	•	Simulate directional strategy
	•	Log win rate

Do not fully implement now — just architecture.

⸻

OUTPUT REQUIRED
	1.	Updated strategy_builder.py (premium fix)
	2.	Updated position_sizer.py (safe Kelly)
	3.	Updated range_predictor.py (fat-tail range)
	4.	New directional_signal.py
	5.	Decision engine modification
	6.	Config.yaml additions
	7.	Clean architecture diagram
	8.	Order of implementation

Provide production-ready structure.

⸻

END OF PROMPT


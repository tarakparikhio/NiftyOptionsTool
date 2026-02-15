# 🚀 NIFTY OPTIONS PLATFORM - COMPLETE GUIDE

**Version:** v2.1-optimized | **Date:** February 15, 2026

---

## 📖 TABLE OF CONTENTS

1. [Quick Start](#quick-start)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Setup & Installation](#setup)
5. [Usage](#usage)
6. [API Reference](#api)
7. [Troubleshooting](#troubleshooting)
8. [Changelog](#changelog)

---

## 🎯 QUICK START

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/NiftyOptionTool
cd NiftyOptionTool

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app_pro.py
```

### Manual CSV Upload (Required)
Upload NSE option chain CSV files via the dashboard sidebar.

Uploads are saved to:
```
data/uploads/
```

---

## 🏗️ ARCHITECTURE

### File Structure
```
NiftyOptionTool/
├── app_pro.py                    # Main dashboard (1683 lines)
├── data_loader.py                # Data ingestion
├── metrics.py                    # PCR, OI, IV metrics
├── visualization.py              # Charts & heatmaps
├── insights.py                   # Trading insights
├── analysis/
│   ├── strategy_builder.py      # Strategy Builder V2 (professional)
│   ├── strategy_ui.py            # Strategy UI components
│   ├── decision_engine.py        # Trade decision logic
│   ├── risk_engine.py            # Risk analytics
│   ├── position_sizer.py         # Position sizing (Kelly, fixed)
│   ├── range_predictor.py        # VIX-based range prediction
│   └── directional_signal.py    # RSI + PCR directional signals
├── api_clients/
│   ├── market_data.py            # NIFTY/VIX data fetcher
│   └── nse_option_chain.py       # NSE API client (Akamai-blocked)
├── data/uploads/                # Manual upload history
├── utils/
│   ├── config_loader.py
│   ├── date_utils.py
│   ├── file_manager.py
│   └── greeks_calculator.py
├── data/
│   ├── uploads/                  # Manual upload history
│   ├── raw/                      # Historical data
│   └── reference/                # NIFTY close, VIX data
└── tests/                        # Test suite
```

### Data Flow
```
Manual CSV Upload → data/uploads/*.csv
         ↓
      Upload History Selection
         ↓
    Metrics → Visualizations → Insights
```

---

## ✨ FEATURES

### Dashboard Tabs (Desktop)
1. **📊 Summary** - Quick metrics (PCR, Max Pain, Range, Signals)
2. **🎯 Positioning** - OI heatmap, top strikes, PCR evolution
3. **📈 Volatility** - IV analysis, skew, volatility surface
4. **📊 Historical** - Candlestick chart, support/resistance
5. **🎨 Strategy Builder** - Multi-leg strategy payoff analyzer
6. **🎲 Decision Engine** - EV, trade scoring, Monte Carlo, AI signals

### Mobile Mode (3 Tabs)
1. **📊 Quick Summary** - Essential metrics only
2. **📈 Range & Volatility** - Range prediction
3. **🎯 Positioning** - Top 3 CE/PE with context

### Key Features

**1. Manual CSV Upload**
- Upload via dashboard sidebar
- Upload history with metadata

**2. OI Analysis**
- Heatmap (±5% strikes for speed)
- Top 3 CE/PE with directional signals
- PCR-based context (bullish/bearish/neutral)
- OI concentration metrics

**3. Strategy Builder V2**
- Multi-leg strategies (up to 10 legs)
- Real-time payoff charts
- Breakeven calculation
- Greeks aggregation
- Probability of Profit (POP)
- Margin estimation
- Presets: Iron Condor, Strangle, Straddle, Bull/Bear Spreads

**4. AI Trade Signal**
- Probability-based recommendation
- Action: SELL_PREMIUM / BUY_PREMIUM / DIRECTIONAL / WAIT
- Confidence: 0-100%
- Factors: PCR (40%), VIX (30%), OI concentration (20%), IV skew (10%)

**5. Decision Engine**
- Volatility edge detection
- Expected value calculation
- Trade quality scoring (0-100)
- Risk of ruin analysis
- Kelly position sizing

**6. Range Prediction**
- VIX-based expected move
- Support/resistance from OI
- Multiple timeframes (daily, weekly)

**7. Directional Signals**
- RSI analysis
- PCR regime classification
- Spot momentum
- Structured recommendations

---

## 🔧 SETUP & INSTALLATION

### Prerequisites
- Python 3.8+
- pip
- 500MB disk space

### Step 1: Install Python Dependencies
```bash
pip install streamlit pandas numpy plotly scipy requests
```

### Step 2: Run Dashboard
```bash
streamlit run app_pro.py
```

Dashboard opens at `http://localhost:8501`

### Step 3: Upload Data
Use the sidebar upload to add your NSE option chain CSV.

---

## 📱 USAGE

### Basic Workflow
1. **Upload CSV** from the sidebar (manual upload)
2. **Open dashboard:** `streamlit run app_pro.py`
3. **Select dataset/expiry** from sidebar
4. **Analyze:**
   - TAB 1: Quick market regime (PCR, VIX, range)
   - TAB 2: OI positioning (top strikes, resistance/support)
   - TAB 5: Build strategy
   - TAB 6: Get AI trade signal

### Reading Top OI Analysis

**Example Output:**
```
📍 Top 3 Call (CE) Positions:
1. Strike 26500 | OI: 250K (12.5%) | +500 pts (+1.9%)
   → Call writers defending resistance at 26500

2. Strike 27000 | OI: 180K (9.0%) | +1000 pts (+3.8%)
   → Strong call writing at 27000 = resistance zone

3. Strike 26000 | OI: 160K (8.0%) | ATM
   → High gamma zone - volatility expected

📍 Top 3 Put (PE) Positions:
1. Strike 25500 | OI: 280K (14.0%) | -500 pts (-1.9%)
   → Put writers defending strong support. PCR: 1.15

2. Strike 25000 | OI: 220K (11.0%) | -1000 pts (-3.8%)
   → Major support level - breakdown target

3. Strike 26000 | OI: 190K (9.5%) | ATM
   → High put interest at ATM - hedging or directional
```

**Interpretation:**
- **High CE OI** = Resistance (call sellers)
- **High PE OI** = Support (put sellers)
- **Distance from spot** = How far to reach level
- **PCR context** = Bullish/bearish bias

### Using AI Trade Signal

1. Go to **TAB 6: Decision Engine**
2. Check **"🎯 AI-Powered Trade Signal"** at top
3. Read output:
   - **Action:** What to do
   - **Confidence:** How sure (>70% = high conviction)
   - **Strategy:** Specific trade recommendation
   - **Reasoning:** Why this signal

**Example:**
```
Signal: 🟢 SELL PREMIUM
Confidence: 85%
Strategy: Iron Condor or Short Strangle
Reasoning: Strong premium selling setup with defined range

Contributing Signals:
- Neutral PCR - range trading favorable
- High VIX (22.5%) - Premium selling favorable
- High OI concentration (68.2%) - Range-bound likely
```

### Building Strategies (TAB 5)

1. Go to **TAB 5: Strategy Builder**
2. Select **preset** (Iron Condor, Strangle, etc.) or build custom
3. **Add legs:**
   - Select CE/PE
   - Buy/Sell
   - Strike price
   - Premium (from option chain)
4. View **payoff chart**
5. Check **metrics:**
   - Max Profit/Loss
   - Breakevens
   - POP (Probability of Profit)
   - Greeks (Delta, Theta, Vega)
   - Margin required

---

## 📚 API REFERENCE

### Key Classes

#### OptionsMetrics
```python
from metrics import OptionsMetrics

metrics = OptionsMetrics(df)
pcr = metrics.compute_pcr()
top_strikes = metrics.get_top_oi_strikes(n=5)
top_context = metrics.get_top_oi_with_context(spot_price, pcr, n=3)
max_pain = metrics.compute_max_pain()
```

#### OptionsVisualizer
```python
from visualization import OptionsVisualizer

viz = OptionsVisualizer(mobile_mode=False)
heatmap = viz.create_oi_heatmap(data, spot_price=26000, strike_range_pct=0.05)
pcr_chart = viz.create_pcr_trend_chart(pcr_trend)
```

#### DecisionEngine
```python
from analysis.decision_engine import DecisionEngine

engine = DecisionEngine()
signal = engine.generate_probability_signal(
    pcr=1.15,
    vix=18.5,
    oi_concentration=68.2,
    iv_skew=2.3
)
# Returns: action, confidence, strategy, reasoning
```

#### Strategy Builder
```python
from analysis.strategy_builder import Strategy, OptionLeg, create_iron_condor

# Create Iron Condor
strategy = create_iron_condor(
    spot_price=26000,
    vix=18.0,
    expiry_date="2026-02-27",
    lot_size=50
)

# Get metrics
max_profit = strategy.get_max_profit()
max_loss = strategy.get_max_loss()
breakevens = strategy.calculate_breakevens()
pop = strategy.calculate_pop()
```

---

## 🐛 TROUBLESHOOTING

### Issue 1: Upload Not Showing Data
**Problem:** Upload succeeded but no data appears in dashboard

**Solutions:**
1. Confirm the CSV is from NSE option-chain page
2. Re-upload and set correct expiry/date
3. Check upload history in the sidebar
4. Verify file saved under `data/uploads/`

### Issue 2: Dashboard Won't Load
**Problem:** ModuleNotFoundError or import errors

**Solutions:**
1. Install all dependencies: `pip install -r requirements.txt`
2. Check Python version: `python3 --version` (need 3.8+)
3. Try: `pip install streamlit pandas numpy plotly scipy`

### Issue 3: No Data in Dashboard
**Problem:** "Upload CSV files to continue"

**Solutions:**
1. Upload a CSV from NSE option-chain page
2. Select an entry from Upload History
3. Confirm `data/uploads/index.jsonl` exists

### Issue 4: Mobile Mode Too Slow
**Problem:** Dashboard loads slowly on mobile

**Solutions:**
1. Enable mobile mode: Checkbox in sidebar
2. Mobile mode removes heavy visualizations
3. Expected load time: <3 seconds
4. Use Wi-Fi instead of cellular data

### Issue 5: Strategy Builder Error
**Problem:** "Strategy Builder dependencies not available"

**Solutions:**
```bash
pip install scipy
```


---

## 📝 CHANGELOG

### v2.1 (February 15, 2026) - Current
**Added:**
- ✅ Manual upload history (data/uploads)
- ✅ Top 3 CE/PE OI with directional context
- ✅ OI heatmap ±5% filter (70% faster)
- ✅ AI-powered trade signal (probability-based)
- ✅ Mobile mode optimization (-55% load time)

**Changed:**
- OI heatmap now shows only ±5% strikes (faster, cleaner)
- Mobile Tab 3 redesigned as "Positioning Summary"
- Decision engine enhanced with probability signal

**Performance:**
- Mobile load: 6.2s → 2.8s (-55%)
- Heatmap render: 3.5s → 1.2s (-66%)

### v2.0 (February 14, 2026)
**Added:**
- ✅ Strategy Builder V2 (professional)
- ✅ Mobile responsive design
- ✅ Cleanup and consolidation

**Removed:**
- Dead code (1,028 lines)
- Duplicate files (plots.py, metrics.py duplicates)
- Legacy dashboards (app.py, streamlit_app.py)

**Changed:**
- Code: 14,606 → 11,831 lines (-19%)
- Docs: 38 → 18 files (-53%)

### v1.0-alpha (February 10, 2026)
**Added:**
- Strategy Builder V2
- Multi-leg strategy payoff
- Greeks aggregation
- Margin estimation
- Probability of Profit (POP)

### v1.0-mvp (January 2026)
**Initial Release:**
- Dashboard with 6 tabs
- Data ingestion (CSV-based)
- Metrics (PCR, OI, IV)
- Range predictor (VIX-based)
- Decision engine
- Risk engine
- Directional signals

---

## 🎯 BEST PRACTICES

### For Intraday Trading
1. **Upload latest CSV** before analysis
2. **Check TAB 1** first (quick regime check)
3. **Review top 3 CE/PE** for key levels
4. **Use AI signal** for direction
5. **Build strategy in TAB 5** if setup is clear

### For Position Trading
1. **Analyze weekly OI trends** (TAB 2)
2. **Check range prediction** (TAB 1)
3. **Build multi-leg strategy** (TAB 5)
4. **Verify with decision engine** (TAB 6)
5. **Monitor daily via dashboard**

### For Options Selling
1. **Check VIX** (high VIX = good for selling)
2. **Verify PCR** (neutral PCR = range trading)
3. **Check OI concentration** (>60% = range-bound)
4. **Use AI signal** (should show SELL_PREMIUM)
5. **Build Iron Condor/Strangle** (TAB 5)

### For Directional Trades
1. **Check directional signals** (TAB 1)
2. **Verify with PCR** (<0.7 bullish, >1.3 bearish)
3. **Check top OI** for support/resistance
4. **Use AI signal** (should show DIRECTIONAL)
5. **Build Bull/Bear Spread** (TAB 5)

---

## 🚀 ADVANCED FEATURES

### Custom Strike Range (Heatmap)
Edit `app_pro.py` line 839:
```python
heatmap = viz.create_oi_heatmap(
    {selected_week: filtered_df},
    spot_price=current_spot,
    strike_range_pct=0.03  # ±3% instead of ±5%
)
```

### Backtesting (Coming in v2.2)
```python
# Future feature
from analysis.backtester import Backtester

bt = Backtester()
results = bt.backtest_strategy(
    strategy=iron_condor,
    start_date="2025-01-01",
    end_date="2026-01-01"
)
```

---

## 📊 PERFORMANCE BENCHMARKS

### Dashboard Load Times
| Device | Desktop Mode | Mobile Mode |
|--------|-------------|-------------|
| MacBook Pro | 3.2s | 2.8s |
| iPhone 15 | 5.1s | 2.8s |
| Android | 5.8s | 3.1s |

### Data Availability Success Rate
- Manual CSV uploads: 100% (when file is present)

### Memory Usage
- Dashboard: ~150MB RAM

---

## 🤝 CONTRIBUTING

See `Prompts/SYSTEM_OPTIMIZER.md` for architecture details and implementation guidelines.

---

## 📞 SUPPORT

**Need help?**
1. Check [Troubleshooting](#troubleshooting) section
2. Check Streamlit logs for upload errors
3. Check GitHub issues

---

## 📄 LICENSE

MIT License - See LICENSE file

---

## 🎉 QUICK REFERENCE

**Start Dashboard:**
```bash
streamlit run app_pro.py
```

**Upload Data:**
Use the sidebar upload to add CSV files

**Test Features:**
```bash
python3 tests/test_v2.1_features.py
```

**Data Location:**
- Uploads: `data/uploads/`
- Reference: `data/reference/`

---

**Built with ❤️ for NIFTY Options Traders**

**Version:** v2.1-optimized | **Last Updated:** February 15, 2026

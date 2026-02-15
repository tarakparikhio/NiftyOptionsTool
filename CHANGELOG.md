# Changelog

All notable changes to the NiftyOptionTool project.

---

## [2.0.0-cleanup] - February 15, 2026

### 🧹 Architecture Cleanup & Simplification

**Major Refactoring:**
- Eliminated 2,775 lines of dead/duplicate/legacy code (-19%)
- Unified strategy builder to professional V2 architecture
- Archived legacy dashboard versions
- Improved mobile responsiveness

**Removed:**
- Dead code: ~1,028 lines (duplicate visualization, metrics modules)
- Legacy code: ~1,318 lines (old dashboards archived)
- Duplicate strategy builder: ~450 lines (migrated to V2)

**Total Impact:** 14,606 → 11,831 lines (-19%)

### 📦 Stage 1: Low-Risk Cleanup
- ❌ Deleted `dashboards/plots.py` (544 lines) - exact duplicate
- ❌ Deleted `analysis/metrics.py` (484 lines) - exact duplicate
- 📦 Archived `app.py` (830 lines) → `archive/legacy_v1.0/app_legacy.py`
- 📦 Archived `dashboards/streamlit_app.py` (488 lines)
- ✏️ Updated `start.sh` to handle legacy dashboard deprecation

### 🔄 Stage 2: Strategy Builder Migration
- 📦 Archived old `analysis/strategy_builder.py` (453 lines)
- ✅ Promoted `strategy_builder_v2.py` → `strategy_builder.py` (614 lines)
- ✏️ Updated all active imports (`app_pro.py`, `strategy_ui.py`)
- 📝 Marked legacy usage in example files (`directional_workflow.py`, `test_directional_engine.py`)
- ✅ All tests passing (6/6 strategy builder tests)

**Benefits:**
- Single unified strategy builder API
- Professional features (POP, Greeks, margin estimation, dual payoff charts)
- Cleaner import structure
- Reduced maintenance burden

---

## [1.0.0-alpha] - February 15, 2026

### 🎉 Strategy Builder V2 - Professional Features

**New Capabilities:**
1. ✅ Probability of Profit (POP) calculation using lognormal distribution
2. ✅ Dual payoff curves (expiry + mark-to-market)
3. ✅ Greeks aggregation (Delta, Gamma, Theta, Vega)
4. ✅ Precise breakeven solver using root-finding (scipy.optimize.brentq)
5. ✅ Margin estimation (NRML/defined risk logic)
6. ✅ Strategy presets (Iron Condor, Strangle, Straddle)
7. ✅ Custom multi-leg builder (unlimited legs)
8. ✅ Risk metrics panel with 3-column layout
9. ✅ Mobile-responsive design

**Files Added:**
- `analysis/strategy_builder_v2.py` (681 lines → now `strategy_builder.py`)
- `analysis/strategy_ui.py` (607 lines)
- `tests/test_strategy_logic.py` (260 lines)
- `docs/STRATEGY_BUILDER_UPGRADE.md` (370 lines)

**Configuration:**
- Enhanced `config.yaml` with strategies section
- Strike selection delta ranges (aggressive/moderate/conservative)
- NIFTY lot size and margin multiplier settings

**Integration:**
- TAB 5: Strategy Builder (desktop mode)
- TAB 6: Decision & Risk analysis enhanced
- Mobile mode: 3-tab layout (Summary, Range, Positioning)
- Desktop mode: 6-tab layout (includes Historical, Strategy, Decision)

---

## [1.0.0-mvp] - February 2026

### 📊 Phase 3: Directional Trading Engine

**New Components:**
1. **DirectionalSignalEngine** (`analysis/directional_signal.py` - 273 lines)
   - RSI calculation (14-period default)
   - PCR-based directional bias
   - Signal confidence scoring

2. **RangePredictor** (`analysis/range_predictor.py` - 436 lines)
   - Statistical models (ATR, Bollinger)
   - Rule-based models (support/resistance)
   - IV-based models (straddle width)
   - Fat-tail distribution awareness

3. **PositionSizer** (`analysis/position_sizer.py` - 489 lines)
   - Kelly Criterion with sample size adjustment
   - Fixed percentage sizing
   - Volatility-based sizing
   - Conservative default: 2% per trade

4. **RiskEngine** (`analysis/risk_engine.py` - 441 lines)
   - Monte Carlo simulation (10,000 paths)
   - Fat-tail risk modeling
   - Win rate vs profit factor analysis
   - Risk of ruin calculation

5. **DecisionEngine** (`analysis/decision_engine.py` - 627 lines)
   - Unified directional + volatility signals
   - Strategy recommendation logic
   - Risk-adjusted position sizing

**Dashboard Integration:**
- TAB 1: Quick Summary with directional bias
- TAB 2: Range & Volatility predictions
- TAB 6: Decision & Risk engine integration

**Mathematical Validation:**
- Greeks calculations verified
- POP logic validated
- Risk engine Monte Carlo tested
- Position sizing Kelly Criterion validated

---

## [0.9.0] - February 2026

### 🎨 Phase 2: Mobile Responsiveness & UX

**Mobile Mode Implementation:**
- Responsive layout detection
- 3-tab mobile layout vs 6-tab desktop
- Optimized chart sizing for mobile
- Toggle switch in sidebar
- Advanced features hidden on mobile (TAB 4-6)

**UI Enhancements:**
- Dark mode professional theme
- Improved tab organization
- Better metric visualization
- Cleaner spacing and typography

**Files Modified:**
- `app_pro.py` - Mobile mode detection and conditional rendering
- `visualization.py` - Mobile-aware chart sizing
- Added custom CSS for responsive breakpoints

---

## [0.8.0] - February 2026

### 📈 Phase 1: Core Analytics Foundation

**Data Infrastructure:**
- CSV-based data ingestion
- Historical data caching
- Multi-week comparison support
- Reference data integration (NIFTY close, VIX)

**Metrics Engine:**
- PCR (Put-Call Ratio) calculation
- OI (Open Interest) concentration analysis
- IV (Implied Volatility) skew detection
- Strike-level metrics aggregation

**Visualization:**
- Interactive Plotly charts
- OI change heatmaps
- PCR trend analysis
- IV surface snapshots
- Strike distribution curves

**Dashboard:**
- Streamlit-based interface
- Multi-tab organization
- Sidebar controls
- Historical data selection

**Files:**
- `data_loader.py` (445 lines)
- `metrics.py` (484 lines)
- `visualization.py` (992 lines)
- `insights.py` (485 lines)
- `app_pro.py` (initial version)

---

## [0.5.0] - January 2026

### 🏗️ Initial Setup

**Project Structure:**
- Folder organization (data/, analysis/, utils/, dashboards/)
- Git repository initialization
- Requirements management
- Configuration system (`config.yaml`)

**Utilities:**
- Date utilities for expiry handling
- File management helpers
- Greeks calculator (Black-Scholes)
- Trade logger (JSONL format)

**API Clients:**
- NSE option chain client (Akamai-blocked, see NSE_API_STATUS.md)
- Market data client structure

**Documentation:**
- README.md
- QUICK_START.md
- Architecture documentation
- Deployment guide

---

## Future Roadmap

### v2.1 (Planned)
- [ ] Stage 3: Monolith refactor (split app_pro.py → ui/ + core/)
- [ ] Enhanced NSE data fetching (browser automation)
- [ ] Backtesting framework
- [ ] Trade execution integration (paper trading)

### v3.0 (Future)
- [ ] Real-time data streaming
- [ ] Portfolio management
- [ ] Multi-strategy comparison
- [ ] Performance analytics dashboard
- [ ] Alert system (Telegram/Email)

---

## Notes

**Breaking Changes:**
- v2.0: Legacy dashboards archived (use app_pro.py only)
- v2.0: Old strategy_builder API deprecated (use V2)
- v1.0: Tab structure changed (3 mobile, 6 desktop)

**Dependencies:**
- Python 3.13+ required
- scipy required for V2 strategy builder
- streamlit, pandas, numpy, plotly core

**Known Issues:**
- NSE API blocked by Akamai (manual CSV upload required)
- Large CSV files may be slow (caching helps)
- Strategy builder not available on mobile (desktop only)

---

**Legend:**
- ✅ Complete
- ⚠️ Partial/Deprecated
- ❌ Removed
- 📦 Archived
- ✏️ Modified
- 📝 Documented

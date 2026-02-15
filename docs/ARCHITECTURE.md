    # File Architecture & Feature Mapping

    > Technical reference for development and extension

    ---

    ## 📊 Core Dashboard Files

    ### **app_pro.py** (814 lines) - Professional Dashboard
    **Purpose**: Production-ready trader-focused interface  
    **Features**:
    - ⚡ **NEW**: Live NSE / Historical mode toggle
    - 5 trader-focused tabs (Overview, Positioning, Volatility, Historical, Strategy Builder)
    - Market regime classification (Bullish/Bearish/Compression/Expansion)
    - Visual range prediction with confidence bands
    - Auto-strategy suggestions based on regime
    - Real-time spot/VIX detection
    - Dark mode optimized UI
    - Live data fetching with caching (5-min TTL)

    **Key Functions**:
    - `get_regime_badge()` - Regime classification logic
    - `create_range_visual()` - Range prediction chart
    - `suggest_strategy()` - Auto-strategy recommendation
    - `load_data()` - Cached data loading (1-hour TTL)

    **Data Modes**:
    - 🔴 **Live NSE**: Fetch current data from NSE API (Phase 1)
    - 📂 **Historical**: Use saved weekly CSV snapshots

    **Dependencies**: data_loader, metrics, visualization, insights, analysis modules

    ---

    ### **app.py** (713 lines) - Legacy Dashboard
    **Purpose**: Original analyst-oriented interface  
    **Features**:
    - 6 generic tabs (Overview, Positioning, IV Analysis, Migration, Insights, Advanced Features)
    - File upload capability
    - Week-over-week comparison
    - Advanced feature sandbox

    **Use Case**: Development testing, feature prototyping

    ---

    ## 📦 Data Processing Layer

    ### **data_loader.py** (454 lines) - NSE CSV Parser + Live Loader
    **Purpose**: Load and transform NSE option chain data  
    **Key Class**: `OptionsDataLoader`

    **Features**:
    - Parse NSE merged CSV format (CALLS | STRIKE | PUTS)
    - ⚡ **NEW**: Load live data via NSE API
    - Auto-detect spot price from OI concentration
    - Add derived columns (Moneyness, Expiry_Quarter, Strike_Distance_Pct)
    - Week-over-week comparison
    - Multi-expiry handling

    **Key Methods**:
    - `load_all_weeks()` - Load historical weekly folders
    - `load_live_chain()` - ⚡ **NEW**: Fetch live data from NSE
    - `add_derived_columns()` - Feature engineering
    - `compute_week_over_week_changes()` - WoW metrics
    - `_parse_nse_csv()` - NSE format parser

    **Data Sources**:
    - Historical: CSV files in `data/raw/monthly/` folders
    - Live: NSE API via `NSEOptionChainClient`

    **Output Schema**:
    ```
    Strike, Option_Type, OI, OI_Change, Volume, IV, LTP, Bid, Ask
    Expiry, Week, Spot_Price, Strike_Distance_Pct, Moneyness, Expiry_Quarter
    ```

    **Used By**: app_pro.py, app.py
    - Handle multiple expiries and quarters
    - Week-based data organization

    **Key Methods**:
    - `load_all_weeks()` - Load all weeks from folder
    - `_parse_nse_csv()` - Parse NSE format
    - `add_derived_columns()` - Add calculated fields
    - `_estimate_spot_price()` - Infer spot from OI
    - `_classify_moneyness()` - ATM/ITM/OTM classification

    **Input**: `data/raw/monthly/WeekName/*.csv`  
    **Output**: Dict[week_name, DataFrame]

    ---

    ### **metrics.py** (485 lines) - Options Metrics Engine
    **Purpose**: Compute positioning intelligence metrics  
    **Key Class**: `OptionsMetrics`, `MultiWeekMetrics`

    **Features**:
    - **PCR (Put-Call Ratio)**: OI-based sentiment
    - **Max Pain**: Strike where writers lose least
    - **IV Skew**: ATM/ITM/OTM volatility spread
    - **OI Concentration**: Top-N strike dominance
    - **Support/Resistance**: High-OI strike levels
    - **Volume Dominance**: CE vs PE flow

    **Key Methods**:
    - `compute_pcr()` - Put-call ratio
    - `compute_max_pain()` - Max pain calculation
    - `compute_iv_skew()` - IV skew metrics
    - `get_top_oi_strikes()` - Top OI strikes
    - `get_support_resistance_levels()` - Key levels
    - `compute_oi_concentration()` - Concentration ratio

    **Used By**: app_pro.py, app.py, analysis modules

    ---

    ### **visualization.py** (545 lines) - Plotly Charts
    **Purpose**: Create interactive visualizations  
    **Key Class**: `OptionsVisualizer`

    **Features**:
    - **OI Heatmap**: Strike vs week OI changes
    - **IV Surface**: Volatility skew across strikes
    - **PCR Trend**: Put-call ratio evolution
    - **Strike Migration**: OI movement over time
    - **OI Distribution**: Call/Put distribution curve

    **Key Methods**:
    - `create_oi_heatmap()` - OI heatmap
    - `create_iv_surface()` - IV surface chart
    - `create_pcr_trend_chart()` - PCR trend
    - `create_strike_migration_chart()` - Migration flow
    - `create_oi_distribution()` - Distribution bars

    **Theme**: Dark mode by default (`plotly_dark`)

    **Used By**: app_pro.py, app.py

    ---

    ### **insights.py** (486 lines) - Pattern Detection
    **Purpose**: Detect structural patterns in positioning  
    **Key Class**: `InsightsEngine`

    **Features**:
    - 15+ pre-configured pattern rules
    - Structural change detection
    - Anomaly identification
    - Severity classification (INFO/WARNING/CRITICAL)

    **Pattern Categories**:
    1. **PCR Extremes**: Bearish/bullish PCR signals
    2. **OI Imbalance**: Asymmetric positioning
    3. **IV Expansion**: Volatility regime shifts
    4. **Volume Surges**: Unusual activity
    5. **Strike Concentration**: Defense level identification

    **Key Methods**:
    - `generate_insights()` - Run all pattern checks
    - `check_pcr_extremes()` - PCR threshold checks
    - `check_oi_concentration()` - Concentration analysis
    - `check_iv_expansion()` - Volatility spikes

    **Output Format**: List[Dict] with severity, message, confidence

    ---

    ## 🔬 Analysis Subsystems

    ### **analysis/range_predictor.py** (388 lines)
    **Purpose**: Predict next-day trading range  
    **Key Class**: `RangePredictor`

    **Methods** (4 prediction techniques):
    1. `predict_statistical()` - ATR-based with VIX scaling
    2. `predict_rule_based()` - PCR + concentration thresholds
    3. `predict_iv_based()` - ATM IV expansion
    4. `predict_ensemble()` - Weighted average with confidence

    **Inputs**: 
    - Option chain DataFrame
    - Historical OHLC data (30-day)
    - Current VIX, spot price

    **Output**: `{lower_range, upper_range, confidence, method_breakdown}`

    **Used By**: Tab 1 (Overview) range visualization

    ---

    ### **analysis/strategy_builder.py** (426 lines)
    **Purpose**: Build option strategies with P&L profiles  
    **Key Class**: `StrategyBuilder`

    **Strategies** (7 types):
    1. Iron Condor
    2. Long/Short Straddle
    3. Strangle
    4. Bull Call Spread
    5. Bear Put Spread
    6. Butterfly
    7. Custom combinations

    **Key Methods**:
    - `create_strategy()` - Build strategy by name
    - `compute_pnl_profile()` - Calculate P&L at expiry
    - `get_max_profit()` - Max profit potential
    - `get_max_loss()` - Max loss potential

    **Used By**: Tab 5 (Strategy Builder)

    ---

    ### **analysis/comparisons.py** (349 lines)
    **Purpose**: Week-over-week analysis  
    **Key Class**: `ComparisonEngine`

    **Features**:
    - Week-over-week changes (OI, IV, Volume)
    - PCR evolution tracking
    - IV evolution across weeks
    - Max OI shift detection

    **Key Methods**:
    - `compute_wow_changes()` - WoW delta calculation
    - `compute_pcr_evolution()` - PCR trend
    - `compute_iv_evolution()` - IV trend
    - `get_max_oi_shifts()` - Largest OI movements

    **Used By**: Tab 4 (Historical Comparison)

    ---

    ### **analysis/insights.py** (duplicate of root insights.py)
    **Status**: Redundant, can be removed

    ---

    ## 🌐 API Integration Layer

    ### **api_clients/nse_option_chain.py** (428 lines) - ⚡ NEW
    **Purpose**: Live NSE option chain data fetching  
    **Key Class**: `NSEOptionChainClient`

    **Features**:
    - Session management with proper NSE cookies
    - Retry logic with exponential backoff (3 attempts)
    - Akamai anti-bot header handling
    - Local caching (5-minute TTL)
    - Graceful fallback to cached data
    - Expiry date extraction
    - DataFrame standardization

    **Key Methods**:
    - `get_raw_option_chain()` - Fetch raw JSON from NSE
    - `get_expiry_dates()` - List available expiries
    - `get_option_chain_by_expiry()` - Fetch for specific expiry
    - `parse_to_dataframe()` - Convert to standardized format
    - `save_cache()` / `load_cache()` - Cache management
    - `is_cache_valid()` - TTL validation

    **Cache Location**: `data/cache/nifty_option_chain_YYYYMMDD_<expiry>.csv`

    **Current Status**: 
    - ✅ Fully implemented with production-ready code
    - ⚠️ NSE API blocked by Akamai bot protection
    - 💡 See `NSE_API_STATUS.md` for workarounds
    
    **Used By**: data_loader.py (`load_live_chain()`), app_pro.py (Live mode)

    ---

    ### **api_clients/market_data.py** (326 lines)
    **Purpose**: Fetch live market data  
    **Key Class**: `MarketDataClient`

    **Data Sources**:
    - Yahoo Finance (^NSEI, ^INDIAVIX)
    - NSE India (fallback)
    - Local cache (CSV persistence)

    **Features**:
    - Live Nifty 50 data (OHLC)
    - India VIX fetching
    - Cache management (TTL-based)
    - Graceful fallback on API failure

    **Key Methods**:
    - `fetch_nifty()` - Current Nifty data
    - `fetch_vix()` - Current VIX
    - `_fetch_yahoo_finance()` - Yahoo API wrapper
    - `_cache_nifty_data()` - Persist to CSV

    **Cache Files**: `data/reference/nifty_close.csv`, `data/reference/vix.csv`

    **Used By**: app_pro.py for spot/VIX detection

    ---

    ## 🛠️ Utilities

    ### **utils/assertion_rules.py** (272 lines)
    **Purpose**: Rule-based market regime detection  
    **Key Class**: `AssertionEngine`

    **Rules** (8 pre-configured):
    1. Extreme PCR (>1.5 or <0.5)
    2. High VIX (>25)
    3. Max Pain divergence (>5%)
    4. OI concentration (>70%)
    5. IV expansion (>30% daily)
    6. Put skew extreme (>10%)
    7. Call buildup at resistance
    8. Put buildup at support

    **Key Methods**:
    - `evaluate_all()` - Run all rule checks
    - `add_rule()` - Register custom rule
    - `evaluate_rule()` - Single rule execution

    **Output**: List of triggered rules with confidence scores

    **Used By**: Tab 1 (Overview) - Active Alerts section

    ---

    ### **utils/config_loader.py** (97 lines)
    **Purpose**: Load YAML configuration  
    **Key Class**: `ConfigLoader`

    **Features**:
    - Load `config.yaml` settings
    - Validate configuration
    - Provide defaults

    **Config Structure**:
    ```yaml
    data:
    folder: "data/raw/monthly"
    metrics:
    pcr_threshold: 1.3
    vix_high: 20
    strategies:
    default_dte: 7
    ```

    ---

    ### **utils/date_utils.py** (143 lines)
    **Purpose**: Date and expiry utilities  
    **Key Functions**:
    - `get_next_expiry()` - Calculate next Thursday expiry
    - `get_dte()` - Days to expiry
    - `is_expiry_week()` - Check if current week is expiry
    - `get_quarter()` - Map date to quarter

    **Used By**: data_loader, metrics modules

    ---

    ### **utils/io_helpers.py** (407 lines)
    **Status**: Duplicate of data_loader.py - can be removed

    ---

    ## 📝 Configuration

    ### **.streamlit/config.toml**
    **Purpose**: Streamlit app configuration

    **Settings**:
    - **Theme**: Dark mode colors
    - **Server**: Port 8501, headless mode
    - **Browser**: Disable analytics

    **Colors**:
    - Primary: Cyan (#00d9ff)
    - Background: Dark (#0e1117)
    - Text: White (#fafafa)

    ---

    ### **config.yaml**
    **Purpose**: Application configuration

    **Sections**:
    - Data paths
    - Metric thresholds
    - Strategy defaults
    - API settings

    ---

    ### **requirements.txt**
    **Purpose**: Python dependencies

    **Core**:
    - streamlit >= 1.54.0
    - pandas >= 2.0.0
    - plotly >= 5.18.0
    - yfinance >= 0.2.28
    - scipy, numpy, scikit-learn

    ---

    ## 🚀 Entry Points

    ### **start.sh** (NEW - Unified Startup)
    **Purpose**: Single script for all operations  
    **Features**:
    - Interactive menu
    - Start/stop dashboard
    - Verify installation
    - View logs
    - Install dependencies

    **Usage**:
    ```bash
    ./start.sh           # Interactive menu
    ./start.sh pro       # Start professional dashboard
    ./start.sh stop      # Stop dashboard
    ./start.sh verify    # Verify installation
    ```

    ---

    ### **verify.py**
    **Purpose**: Verify all dependencies installed  
    **Checks**:
    - Python packages
    - Module imports
    - Data directories

    ---

    ### **run_analysis.py**
    **Purpose**: Command-line analysis runner  
    **Features**:
    - Batch processing
    - CSV output
    - Summary reports

    ---

    ## 📊 Data Structure

    ### **Input Data Format**

    **NSE CSV Structure**:
    ```
    CALLS_OI | CALLS_Chng_in_OI | ... | STRIKE | ... | PUTS_OI | PUTS_Chng_in_OI
    100000   | 5000              | ... | 26000  | ... | 150000  | 8000
    ```

    **Folder Structure**:
    ```
    data/raw/monthly/
    └── Feb14/
        ├── option-chain-ED-NIFTY-30-Mar-2026.csv
        ├── option-chain-ED-NIFTY-30-Jun-2026.csv
        └── ...
    ```

    ### **Processed DataFrame Schema**

    **Columns** (after `add_derived_columns()`):
    - `Strike` - Strike price
    - `Option_Type` - CE or PE
    - `Expiry` - Expiry date
    - `Expiry_Quarter` - Quarter identifier
    - `OI` - Combined open interest
    - `OI_Change` - Change in OI
    - `Volume` - Trading volume
    - `IV` - Implied volatility
    - `Spot_Price` - Current spot (estimated)
    - `Strike_Distance_Pct` - % distance from spot
    - `Moneyness` - ATM/ITM/OTM classification

    ---

    ## 🎯 Feature-to-File Mapping

    | Feature | Primary File | Supporting Files |
    |---------|-------------|------------------|
    | **Dashboard UI** | app_pro.py | visualization.py, metrics.py |
    | **Data Loading** | data_loader.py | utils/io_helpers.py |
    | **Metrics** | metrics.py | - |
    | **Charts** | visualization.py | - |
    | **Pattern Detection** | insights.py | - |
    | **Range Prediction** | analysis/range_predictor.py | - |
    | **Strategy Builder** | analysis/strategy_builder.py | - |
    | **WoW Comparison** | analysis/comparisons.py | - |
    | **Market Data API** | api_clients/market_data.py | - |
    | **Regime Rules** | utils/assertion_rules.py | - |
    | **Configuration** | utils/config_loader.py | config.yaml |

    ---

    ## 🔧 Extension Points

    ### **Add New Strategy**
    1. Edit `analysis/strategy_builder.py`
    2. Add method in `StrategyBuilder` class
    3. Register in `get_all_strategies()`
    4. Update UI in `app_pro.py` Tab 5

    ### **Add New Metric**
    1. Edit `metrics.py`
    2. Add method in `OptionsMetrics` class
    3. Use in `app_pro.py` or `app.py`

    ### **Add New Chart**
    1. Edit `visualization.py`
    2. Add method in `OptionsVisualizer` class
    3. Call from dashboard tabs

    ### **Add New Pattern**
    1. Edit `insights.py` or `utils/assertion_rules.py`
    2. Add detection logic
    3. Display in Tab 1 (Active Alerts)

    ### **Add New Data Source**
    1. Edit `api_clients/market_data.py`
    2. Add fetch method
    3. Update cache logic
    4. Use in `app_pro.py`

    ---

    ## 📁 Deprecated Files

    **Can be removed** (redundant or obsolete):
    - `restart_dashboard.sh` - Replaced by start.sh
    - `START_HERE.py` - Replaced by start.sh
    - `utils/io_helpers.py` - Duplicate of data_loader.py
    - `analysis/insights.py` - Duplicate of root insights.py
    - `README_PLATFORM.md` - Consolidated
    - `🚀 START HERE.md` - Consolidated
    - `FILE_GUIDE.txt` - Replaced by this file

    ---

    ## 🚀 Quick Development Guide

    ### **Add a New Feature**
    1. **Identify Layer**: Data/Metrics/Analysis/Visualization/UI
    2. **Create Module**: Add to appropriate folder
    3. **Import**: Add to relevant dashboard file
    4. **UI Integration**: Add to app_pro.py tabs
    5. **Test**: Use start.sh verify

    ### **Modify Existing Feature**
    1. **Find File**: Use this mapping document
    2. **Edit Function**: Modify specific method
    3. **Test**: Restart dashboard with start.sh
    4. **Verify**: Check UI reflects changes

    ### **Debug Issues**
    1. **Check Logs**: `tail -f streamlit.log`
    2. **Verify Data**: Use debug panel in sidebar
    3. **Test Imports**: `python3 verify.py`
    4. **Check Errors**: Browser console + streamlit.log

    ---

    **Last Updated**: Version 2.1 (February 2026)  
    **Maintainer**: Professional Trader Edition

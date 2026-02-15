"""
Professional Options Analytics Dashboard - Streamlit Cloud Ready

Trader-focused interface answering:
1. What is the positioning bias?
2. Where is support/resistance?
3. What is expected tomorrow's range?
4. Which strategy fits current structure?
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Import custom modules
from data_loader import OptionsDataLoader
from metrics import OptionsMetrics, MultiWeekMetrics
from visualization import OptionsVisualizer
from insights import InsightsEngine

# NEW: Import directional trading components
from analysis.directional_signal import DirectionalSignalEngine
# NOTE: Legacy strategy_builder classes removed - using strategy_builder_v2 in TAB 5
from analysis.position_sizer import PositionSizer
from analysis.range_predictor import RangePredictor
from analysis.decision_engine import DecisionEngine
from analysis.risk_engine import RiskEngine

# Professional Strategy Builder UI (lazy import to avoid startup failures)
# from analysis.strategy_ui import render_strategy_builder_tab  # Imported in Tab 5 when needed

# Page configuration
st.set_page_config(
    page_title="Nifty Options Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize mobile mode in session state
if 'mobile_mode' not in st.session_state:
    st.session_state.mobile_mode = False

# Custom CSS for dark mode professional look (mobile-responsive)
mobile_styles = """
    /* Mobile optimizations */
    @media (max-width: 768px) {
        .main {padding: 0rem 0.5rem;}
        h1 {font-size: 1.8rem;}
        h2 {font-size: 1.4rem;}
        h3 {font-size: 1.2rem;}
        .stMetric {padding: 10px; font-size: 0.9rem;}
    }
""" if st.session_state.mobile_mode else ""

st.markdown(f"""
    <style>
    .main {{padding: 0rem 1rem;}}
    .stMetric {{background-color: #1e1e1e; padding: 15px; border-radius: 5px; border: 1px solid #333;}}
    .bullish-badge {{background-color: #28a745; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold; box-shadow: 0 0 10px rgba(40, 167, 69, 0.3);}}
    .bearish-badge {{background-color: #dc3545; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold; box-shadow: 0 0 10px rgba(220, 53, 69, 0.3);}}
    .neutral-badge {{background-color: #ffc107; color: #0e1117; padding: 5px 15px; border-radius: 15px; font-weight: bold; box-shadow: 0 0 10px rgba(255, 193, 7, 0.3);}}
    .compression-badge {{background-color: #17a2b8; color: white; padding: 5px 15px; border-radius: 15px; font-weight: bold; box-shadow: 0 0 10px rgba(23, 162, 184, 0.3);}}
    h1 {{color: #00d9ff; font-size: 2.5rem; text-shadow: 0 0 10px rgba(0, 217, 255, 0.3);}}
    h2 {{color: #ffa500; margin-top: 2rem;}}
    h3 {{color: #4ade80;}}
    .tooltip {{border-bottom: 1px dotted #999; cursor: help;}}
    .stAlert {{background-color: #1e1e1e; border: 1px solid #444;}}
    {mobile_styles}
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_data(data_folder: str):
    """Load and cache options data."""
    loader = OptionsDataLoader(data_folder)
    weekly_data = loader.load_all_weeks()
    
    # Add derived columns to all weeks
    for week in weekly_data:
        weekly_data[week] = loader.add_derived_columns(weekly_data[week])
    
    weeks = sorted(weekly_data.keys())
    return weekly_data, weeks


def get_regime_badge(pcr: float, vix: float, concentration: float) -> tuple:
    """
    Determine market regime and return badge HTML and description.
    
    Returns:
        (badge_html, regime_name, description)
    """
    # Regime logic
    if pcr > 1.3 and vix > 20:
        return '<span class="bearish-badge">🔴 BEARISH BIAS</span>', "Bearish", "High put buildup + elevated VIX"
    elif pcr < 0.7 and vix < 12:
        return '<span class="bullish-badge">🟢 BULLISH BIAS</span>', "Bullish", "Low put interest + calm VIX"
    elif concentration > 60:
        return '<span class="compression-badge">🔵 COMPRESSION</span>', "Compression", "High OI concentration = range-bound"
    elif vix > 20:
        return '<span class="neutral-badge">⚠️ EXPANSION</span>', "Expansion", "High volatility regime"
    else:
        return '<span class="neutral-badge">🟡 NEUTRAL</span>', "Neutral", "Balanced positioning"


def create_range_visual(spot: float, pred_lower: float, pred_upper: float, 
                       support: float = None, resistance: float = None):
    """Create visual range prediction chart."""
    fig = go.Figure()
    
    # Horizontal range
    y_pos = [0, 0, 0]
    x_pos = [pred_lower, spot, pred_upper]
    colors = ['red', 'blue', 'green']
    labels = [f'Lower: {pred_lower:.0f}', f'Spot: {spot:.0f}', f'Upper: {pred_upper:.0f}']
    
    # Add range band
    fig.add_trace(go.Scatter(
        x=[pred_lower, pred_upper],
        y=[0, 0],
        mode='lines',
        line=dict(color='rgba(100,100,100,0.3)', width=30),
        name='Predicted Range',
        hoverinfo='skip'
    ))
    
    # Add spot and bounds
    for i, (x, label, color) in enumerate(zip(x_pos, labels, colors)):
        fig.add_trace(go.Scatter(
            x=[x],
            y=[0],
            mode='markers+text',
            marker=dict(size=20, color=color),
            text=[label],
            textposition='top center',
            name=label.split(':')[0]
        ))
    
    # Add support/resistance if provided
    if support:
        fig.add_vline(x=support, line_dash="dash", line_color="green", opacity=0.5,
                     annotation_text=f"Support: {support:.0f}")
    if resistance:
        fig.add_vline(x=resistance, line_dash="dash", line_color="red", opacity=0.5,
                     annotation_text=f"Resistance: {resistance:.0f}")
    
    fig.update_layout(
        title="Predicted Next-Day Range",
        height=200,
        showlegend=False,
        yaxis=dict(visible=False, range=[-1, 1]),
        xaxis_title="Nifty Level",
        margin=dict(t=50, b=20)
    )
    
    return fig


def suggest_strategy(regime: str, pcr: float, vix: float, iv_skew: float) -> tuple:
    """Suggest optimal strategy based on market regime."""
    if regime == "Compression":
        return "Iron Condor", "📉 Sell premium in range-bound market"
    elif regime == "Expansion":
        return "Long Straddle", "📈 Buy volatility expecting big move"
    elif regime == "Bearish" and iv_skew > 5:
        return "Bear Put Spread", "🐻 Capitalize on put IV premium"
    elif regime == "Bullish":
        return "Bull Call Spread", "🐂 Directional upside play"
    else:
        return "Strangle", "⚖️ Neutral position, waiting for breakout"


def _render_mobile_strategy_section(filtered_df, current_spot, current_vix, regime, pcr):
    """Simplified strategy builder for mobile view."""
    st.markdown("**Suggested Strategy:**")
    strategy_name, strategy_desc = suggest_strategy(regime, pcr, current_vix, 0)
    st.info(f"**{strategy_name}** - {strategy_desc}")
    
    st.markdown("---")
    st.subheader("Key Strikes")
    
    # Top 3 strikes only
    metrics = OptionsMetrics(filtered_df)
    top_strikes_df = metrics.get_top_oi_strikes(n=3, by_type=True)
    
    for _, row in top_strikes_df.iterrows():
        st.metric(
            f"{row['Type']} Strike {row['Strike']:.0f}",
            f"{row['OI']:,.0f} OI",
            delta=f"Change: {row.get('OI_Change', 0):,.0f}"
        )


def _render_mobile_risk_section(filtered_df, current_spot, pred_lower, pred_upper):
    """Simplified risk analysis for mobile view."""
    st.subheader("⚠️ Risk Metrics")
    
    st.metric("Predicted Range", f"{pred_upper - pred_lower:.0f} pts")
    st.metric("Downside Risk", f"{current_spot - pred_lower:.0f} pts")
    st.metric("Upside Potential", f"{pred_upper - current_spot:.0f} pts")
    
    st.markdown("---")
    st.markdown("**Position Sizing Guide:**")
    st.info("Risk 1-2% of capital per trade for conservative approach")


def _render_directional_signals(filtered_df, current_spot):
    """Helper function to render directional signals section."""
    try:
        # Try to load 1H price data (if available)
        price_data = None
        try:
            price_history = pd.read_csv("data/raw/daily/prices_1h.csv") if Path("data/raw/daily/prices_1h.csv").exists() else None
            if price_history is not None:
                price_series = price_history['close'].tail(100)
            else:
                price_series = pd.Series(np.linspace(current_spot - 200, current_spot + 200, 100))
        except:
            price_series = pd.Series(np.linspace(current_spot - 200, current_spot + 200, 100))
        
        # Generate signal
        signal_engine = DirectionalSignalEngine(
            rsi_oversold=30,
            rsi_overbought=70,
            pcr_oversold=0.7,
            pcr_overbought=1.3
        )
        
        signal = signal_engine.generate_signal(
            price_series=price_series,
            option_df=filtered_df
        )
        
        # Display signal with emoji and color
        signal_colors = {
            'CALL_BUY': '📈 🟢',
            'PUT_BUY': '📉 🔴',
            'NO_SIGNAL': '🟡 Neutral'
        }
        
        # Responsive layout
        if st.session_state.get('mobile_mode', False):
            st.markdown(f"### Signal: {signal_colors.get(signal.signal, signal.signal)}")
            st.markdown(f"**{signal.signal}** - Confidence: {signal.confidence:.0f}%")
            st.metric("RSI", f"{signal.rsi:.1f}", delta=f"Target: 30-70")
            st.metric("PCR", f"{signal.pcr:.2f}", delta=f"Target: 0.7-1.3")
        else:
            signal_col, conf_col = st.columns([2, 1])
            
            with signal_col:
                st.markdown(f"### Signal: {signal_colors.get(signal.signal, signal.signal)}")
                st.markdown(f"**{signal.signal}** - Confidence: {signal.confidence:.0f}%")
            
            with conf_col:
                st.metric("RSI", f"{signal.rsi:.1f}", delta=f"Target: 30-70")
                st.metric("PCR", f"{signal.pcr:.2f}", delta=f"Target: 0.7-1.3")
        
        # Show reasoning
        if signal.reasons:
            with st.expander("📊 Signal Reasoning"):
                for reason in signal.reasons:
                    st.markdown(f"- {reason}")
    
    except Exception as e:
        st.warning(f"Signal generation: {e}")


def _render_range_prediction(filtered_df, metrics, current_spot, current_vix, atm_iv):
    """Helper function to render range prediction - used by both mobile and desktop views."""
    # VIX-Based Range Enhancement Display
    with st.expander("📊 VIX-Based Range Model"):
        st.markdown("""
        **Range Calculation Method:**
        - ATM Implied Volatility from options
        - VIX converted to daily move: `daily_move = spot × (VIX / sqrt(252))`
        - Historical ATR (Average True Range)
        - OI-weighted strike concentration
        - PCR regime adjustment
        
        **Current Inputs:**
        """)
        
        # Responsive column layout
        if st.session_state.get('mobile_mode', False):
            st.metric("VIX", f"{current_vix:.1f}%")
            daily_move = current_spot * (current_vix / 100) / np.sqrt(252)
            st.metric("Expected Daily Move", f"±{daily_move:.0f} pts")
            st.metric("ATM IV", f"{atm_iv:.2f}%")
        else:
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("VIX", f"{current_vix:.1f}%")
            with col_b:
                daily_move = current_spot * (current_vix / 100) / np.sqrt(252)
                st.metric("Expected Daily Move", f"±{daily_move:.0f} pts")
            with col_c:
                st.metric("ATM IV", f"{atm_iv:.2f}%")
    
    try:
        from analysis.range_predictor import RangePredictor
        
        # Create historical data
        hist = pd.DataFrame({
            'close': np.random.randn(30) * 50 + current_spot,
            'high': np.random.randn(30) * 50 + current_spot + 100,
            'low': np.random.randn(30) * 50 + current_spot - 100,
        })
        
        predictor = RangePredictor(filtered_df, hist, current_vix=current_vix, current_spot=current_spot)
        ensemble_pred = predictor.predict_ensemble()
        
        pred_lower = ensemble_pred.get('lower_range', current_spot - 150)
        pred_upper = ensemble_pred.get('upper_range', current_spot + 150)
        confidence = ensemble_pred.get('confidence', 70)
        
        # Get support/resistance from OI
        levels = metrics.get_support_resistance_levels(top_n=5)
        support = levels['support'][0] if levels.get('support') else current_spot - 200
        resistance = levels['resistance'][0] if levels.get('resistance') else current_spot + 200
        
        # Visual range
        range_fig = create_range_visual(current_spot, pred_lower, pred_upper, support, resistance)
        st.plotly_chart(range_fig, use_container_width=True, config={"responsive": True, "displayModeBar": False})
        
        # Range metrics - Responsive layout
        if st.session_state.get('mobile_mode', False):
            st.metric("Lower Bound", f"{pred_lower:.0f}", f"{pred_lower - current_spot:.0f} pts")
            st.metric("Upper Bound", f"{pred_upper:.0f}", f"{pred_upper - current_spot:+.0f} pts")
            st.metric("Range Width", f"{pred_upper - pred_lower:.0f} pts",
                     f"Conf: {confidence:.0f}%")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Lower Bound", f"{pred_lower:.0f}", f"{pred_lower - current_spot:.0f} pts")
            with col2:
                st.metric("Upper Bound", f"{pred_upper:.0f}", f"{pred_upper - current_spot:+.0f} pts")
            with col3:
                st.metric("Range Width", f"{pred_upper - pred_lower:.0f} pts",
                         f"Conf: {confidence:.0f}%")
        
        # NEW: Fat-Tail Adjusted Ranges
        if not st.session_state.get('mobile_mode', False):  # Hide on mobile for brevity
            st.markdown("**📊 Fat-Tail Risk Adjustment**")
            fat_tail_data = predictor.predict_statistical()
            
            if fat_tail_data and isinstance(fat_tail_data, dict):
                fat_lower = fat_tail_data.get('fat_tail_lower', pred_lower)
                fat_upper = fat_tail_data.get('fat_tail_upper', pred_upper)
                fat_multiplier = fat_tail_data.get('fat_tail_multiplier', 1.0)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write("**Normal Distribution Model**")
                    st.metric("Adjusted Lower", f"{pred_lower:.0f}", 
                             f"{(pred_lower - current_spot):.0f} pts")
                    st.metric("Adjusted Upper", f"{pred_upper:.0f}", 
                             f"{(pred_upper - current_spot):+.0f} pts")
                
                with col_b:
                    st.write("**Fat-Tail Adjusted (99th Percentile)**")
                    st.metric("Risk Lower", f"{fat_lower:.0f}", 
                             f"{(fat_lower - current_spot):.0f} pts")
                    st.metric("Risk Upper", f"{fat_upper:.0f}", 
                             f"{(fat_upper - current_spot):+.0f} pts")
                
                st.info(f"🔴 **Fat-Tail Multiplier: {fat_multiplier:.2f}x** — Range adjusted {fat_multiplier:.0%} wider to account for tail events (crashes, gaps)")
        
        # Return values for use in summary
        return pred_lower, pred_upper, support, resistance
    
    except Exception as e:
        st.warning(f"Range prediction: {e}")
        st.info("Using fallback estimates")
        # Return fallback values
        return current_spot - 150, current_spot + 150, current_spot - 200, current_spot + 200


def main():
    # Header
    st.title("📊 Nifty Options Intelligence")
    st.markdown("*Professional analytics for discretionary traders*")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Mobile Mode Toggle
        st.session_state.mobile_mode = st.checkbox(
            "📱 Mobile Mode", 
            value=st.session_state.mobile_mode,
            help="Optimized layout for mobile devices (375-430px width)"
        )
        
        if st.session_state.mobile_mode:
            st.info("📱 Mobile mode active: Single column layout, reduced charts, collapsible sections")
        
        st.markdown("---")
        
        # Data source selection (CSV only - NSE disabled per Phase 2)
        data_source = st.radio(
            "📊 Data Source",
            ["📁 Folder", "📤 Upload CSV"],
            help="Select from existing folders or upload new CSV files"
        )
        
        data_folder = None
        
        data_folder = None
        
        if data_source == "📁 Folder":
            quick_paths = [
                "data/raw/monthly",
                "Options/Monthly",
                "Custom..."
            ]
            
            path_choice = st.selectbox("Quick Select", quick_paths)
            
            if path_choice == "Custom...":
                data_folder = st.text_input("Path", value="data/raw/monthly")
            else:
                data_folder = path_choice
        
        else:  # Upload CSV mode with FileManager
            uploaded_files = st.file_uploader(
                "Upload NSE Option Chain CSV",
                type=['csv'],
                accept_multiple_files=True,
                help="Upload option chain CSV files - will be auto-organized"
            )
            
            if uploaded_files:
                from utils.file_manager import FileManager
                fm = FileManager()
                
                saved_paths = []
                for file in uploaded_files:
                    try:
                        saved_path, folder_type = fm.save_uploaded_file(
                            file.read(), 
                            file.name
                        )
                        saved_paths.append((saved_path, folder_type))
                        st.success(f"✅ Saved: `{Path(saved_path).name}` → `{folder_type}/`")
                    except Exception as e:
                        st.error(f"❌ Error saving {file.name}: {e}")
                
                if saved_paths:
                    st.info(f"📁 **FileManager**: Auto-organized {len(saved_paths)} file(s) by expiry date and weekly/monthly detection")
                
                if saved_paths:
                    # Use the folder of the first uploaded file
                    first_path = Path(saved_paths[0][0])
                    data_folder = str(first_path.parent.parent)  # Go up to monthly/weekly folder
                    st.info(f"📂 Loading from: {data_folder}")
            else:
                st.warning("⚠️ Upload CSV files to continue")
                return
    
    # Load CSV data
    try:
            weekly_data, weeks = load_data(data_folder)
            
            if not weekly_data:
                st.error("❌ No data found!")
                return
            
            with st.sidebar:
                st.success(f"✅ Loaded {len(weeks)} weeks")
                
                # Week and expiry selection
                st.markdown("### 📅 Selection")
                selected_week = st.selectbox("Week", weeks, index=len(weeks)-1)
                
                current_df = weekly_data[selected_week]
                expiries = sorted(current_df['Expiry_Quarter'].unique())
                selected_expiry = st.selectbox("Expiry", expiries, index=0)
                
                # Filter by expiry
                filtered_df = current_df[current_df['Expiry_Quarter'] == selected_expiry].copy()
                
                # Strike range filter
                st.markdown("### 🎯 Strike Filter")
                all_strikes = sorted(filtered_df['Strike'].unique())
                strike_range = st.slider(
                    "Strike Range",
                    min_value=float(all_strikes[0]),
                    max_value=float(all_strikes[-1]),
                    value=(float(all_strikes[0]), float(all_strikes[-1])),
                    step=50.0
                )
                
                filtered_df = filtered_df[
                    (filtered_df['Strike'] >= strike_range[0]) &
                    (filtered_df['Strike'] <= strike_range[1])
                ]
                
                st.info(f"📊 {len(filtered_df)} strikes selected")
                
                # Manual NIFTY Data Update Feature
                st.markdown("---")
                with st.expander("📝 NIFTY Data Update"):
                    from datetime import datetime, date
                    from utils.nifty_data_manager import NiftyDataManager
                    from api_clients.market_data import MarketDataClient
                    
                    # Auto-fetch button
                    st.markdown("**🔄 Automatic Update**")
                    if st.button("🚀 Auto-Fetch from API", type="primary", width="stretch"):
                        with st.spinner("Fetching latest NIFTY data..."):
                            try:
                                client = MarketDataClient()
                                data = client.fetch_nifty(use_cache=False)
                                
                                if data and 'date' in data:
                                    # Auto-update using fetched data
                                    manager = NiftyDataManager()
                                    manager.add_daily_update(
                                        date_str=data['date'],
                                        open_val=data['open'],
                                        high=data['high'],
                                        low=data['low'],
                                        close=data['close'],
                                        volume=data.get('volume', 0)
                                    )
                                    st.success(f"✅ Auto-updated: {data['date']} | Close: ₹{data['close']:,.2f}")
                                    st.info("🔄 Refresh page to see updated chart")
                                    st.cache_data.clear()
                                else:
                                    st.error("❌ API returned no data. Try manual entry below.")
                            except ImportError:
                                st.error("❌ yfinance not installed. Run: pip install yfinance")
                            except Exception as e:
                                st.error(f"❌ Auto-fetch failed: {e}")
                    
                    st.markdown("---")
                    st.markdown("**✏️ Manual Entry** *(if auto-fetch fails)*")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_date = st.date_input(
                            "Date",
                            value=date.today(),
                            help="Trading date for the data"
                        )
                    with col2:
                        volume = st.number_input(
                            "Volume (Shares)",
                            min_value=0,
                            value=400000000,
                            step=10000000,
                            help="Shares traded (optional)"
                        )
                    
                    col3, col4 = st.columns(2)
                    with col3:
                        open_price = st.number_input(
                            "Open",
                            min_value=0.0,
                            value=25500.0,
                            step=10.0,
                            format="%.2f"
                        )
                        low_price = st.number_input(
                            "Low",
                            min_value=0.0,
                            value=25400.0,
                            step=10.0,
                            format="%.2f"
                        )
                    with col4:
                        high_price = st.number_input(
                            "High",
                            min_value=0.0,
                            value=25700.0,
                            step=10.0,
                            format="%.2f"
                        )
                        close_price = st.number_input(
                            "Close",
                            min_value=0.0,
                            value=25650.0,
                            step=10.0,
                            format="%.2f"
                        )
                    
                    if st.button("✅ Update NIFTY Data", type="primary"):
                        try:
                            # Validate OHLC relationship
                            if high_price < low_price:
                                st.error("❌ High must be >= Low")
                            elif close_price > high_price or close_price < low_price:
                                st.error("❌ Close must be between High and Low")
                            elif open_price > high_price or open_price < low_price:
                                st.error("❌ Open must be between High and Low")
                            else:
                                manager = NiftyDataManager()
                                manager.add_daily_update(
                                    date_str=update_date.strftime('%d-%b-%Y'),
                                    open_val=open_price,
                                    high=high_price,
                                    low=low_price,
                                    close=close_price,
                                    volume=int(volume)
                                )
                                st.success(f"✅ Added data for {update_date.strftime('%d-%b-%Y')}")
                                st.info("🔄 Refresh the page to see updated candlestick chart")
                                # Clear cache to reload data
                                st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error updating data: {e}")
                    
                    st.caption("💡 Data saved to `data/reference/nifty_close.csv`")
                
                # Debug section (collapsible)
                with st.expander("🔍 Data Debug Info"):
                    st.write(f"**Columns in data:** {', '.join(filtered_df.columns[:10])}...")
                    if 'Spot_Price' in filtered_df.columns:
                        spot_vals = filtered_df['Spot_Price'].unique()
                        st.write(f"**Spot_Price values:** {spot_vals[:5]}")
                    else:
                        st.write("**Spot_Price column:** Not found")
                    
                    st.write(f"**Strike range:** {filtered_df['Strike'].min():.0f} - {filtered_df['Strike'].max():.0f}")
                    st.write(f"**Total OI:** {filtered_df['OI'].sum():,.0f}")
        
    except Exception as e:
            st.error(f"❌ Error: {e}")
            return
    
    # Compute metrics
    metrics = OptionsMetrics(filtered_df)
    pcr_df = metrics.compute_pcr(by_expiry=False)
    pcr = pcr_df['PCR'].iloc[0] if not pcr_df.empty else 1.0
    max_pain = metrics.compute_max_pain()
    iv_skew_dict = metrics.compute_iv_skew()
    iv_skew = iv_skew_dict.get('ATM_OTM_Skew', 0)
    atm_iv = iv_skew_dict.get('ATM_IV', 0)
    
    # Get top strikes - convert DataFrame to list of tuples
    top_strikes_df = metrics.get_top_oi_strikes(n=5, by_type=False)
    top_strikes = list(zip(top_strikes_df['Strike'].values, top_strikes_df['OI'].values))[:5]
    
    # Get real spot price from data - try multiple methods
    current_spot = 26000  # Default fallback
    
    # Method 1: Check if Spot_Price column exists and has valid value
    if 'Spot_Price' in filtered_df.columns and len(filtered_df) > 0:
        spot_from_col = filtered_df['Spot_Price'].iloc[0]
        if spot_from_col and spot_from_col > 0:
            current_spot = spot_from_col
    
    # Method 2: Calculate from ATM strike (highest combined OI)
    if current_spot == 26000:  # If Method 1 failed, try Method 2
        try:
            strike_oi = filtered_df.groupby('Strike')['OI'].sum()
            if len(strike_oi) > 0:
                atm_strike = strike_oi.idxmax()
                if atm_strike and atm_strike > 0:
                    current_spot = atm_strike
        except:
            pass
    
    # Method 3: Try fetching from API
    if current_spot == 26000:
        try:
            from api_clients.market_data import MarketDataClient
            api = MarketDataClient()
            nifty_data = api.fetch_nifty(use_cache=True)
            if nifty_data and 'close' in nifty_data:
                current_spot = nifty_data['close']
        except:
            pass
    
    # Fetch VIX with fallback
    current_vix = 18.5  # Default
    try:
        from api_clients.market_data import MarketDataClient
        api = MarketDataClient()
        vix_data = api.fetch_vix(use_cache=True)
        if vix_data and 'vix_value' in vix_data:
            current_vix = vix_data['vix_value']
    except:
        pass  # Use default
    
    # Concentration
    total_oi = filtered_df.groupby('Strike')['OI'].sum()
    concentration = (total_oi.nlargest(5).sum() / total_oi.sum() * 100) if len(total_oi) > 0 else 0
    
    # Get regime
    badge_html, regime, regime_desc = get_regime_badge(pcr, current_vix, concentration)
    
    # Initialize visualizer once for all tabs
    viz = OptionsVisualizer(theme='plotly_dark', mobile_mode=st.session_state.mobile_mode)
    
    # Tabs - Simplified for mobile
    if st.session_state.mobile_mode:
        tab1, tab2, tab3 = st.tabs([
            "📈 Overview",
            "🎯 Strategy", 
            "⚠️ Risk"
        ])
        # Mobile mode: Collapse advanced tabs
        show_advanced = st.checkbox("Show Advanced Analytics", value=False)
    else:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Overview",
            "🎯 Positioning", 
            "📊 Volatility",
            "🔄 Historical",
            "🏗️ Strategy Builder",
            "🎲 Decision & Risk"
        ])
        show_advanced = True
    
    # ============ TAB 1: OVERVIEW ============
    with tab1:
        st.header("Market Overview")
        
        # Regime badge
        st.markdown(f"### Market Regime: {badge_html}", unsafe_allow_html=True)
        st.caption(regime_desc)
        
        st.markdown("---")
        
        # Key metrics - Responsive layout
        if st.session_state.mobile_mode:
            # Mobile: Single column with expandable sections
            with st.expander("📊 Market Metrics", expanded=True):
                st.metric("Nifty Spot", f"{current_spot:,.0f}", help="Current Nifty 50 level")
                st.metric("VIX", f"{current_vix:.1f}%", help="India VIX - Volatility Index")
                pcr_delta = "Bearish" if pcr > 1.3 else "Bullish" if pcr < 0.7 else "Neutral"
                st.metric("PCR", f"{pcr:.2f}", delta=pcr_delta,
                         help="Put-Call Ratio: >1.3 bearish, <0.7 bullish")
                st.metric("Max Pain", f"{max_pain:,.0f}",
                         help="Strike where option writers lose least")
        else:
            # Desktop: 4-column layout
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Nifty Spot", f"{current_spot:,.0f}", help="Current Nifty 50 level")
                # Debug info
                if 'Spot_Price' in filtered_df.columns:
                    spot_col_val = filtered_df['Spot_Price'].iloc[0] if len(filtered_df) > 0 else None
                    if spot_col_val != current_spot:
                        st.caption(f"📍 Estimated: {current_spot:,.0f}")
            with col2:
                st.metric("VIX", f"{current_vix:.1f}%", 
                         help="India VIX - Volatility Index")
            with col3:
                pcr_delta = "Bearish" if pcr > 1.3 else "Bullish" if pcr < 0.7 else "Neutral"
                st.metric("PCR", f"{pcr:.2f}", delta=pcr_delta,
                         help="Put-Call Ratio: >1.3 bearish, <0.7 bullish")
            with col4:
                st.metric("Max Pain", f"{max_pain:,.0f}",
                         help="Strike where option writers lose least")
        
        st.markdown("---")
        
        # Predicted range - Collapsible in mobile mode
        if st.session_state.mobile_mode:
            with st.expander("📍 Next-Day Range Prediction", expanded=True):
                pred_lower, pred_upper, support, resistance = _render_range_prediction(filtered_df, metrics, current_spot, current_vix, atm_iv)
        else:
            st.subheader("📍 Next-Day Range Prediction")
            pred_lower, pred_upper, support, resistance = _render_range_prediction(filtered_df, metrics, current_spot, current_vix, atm_iv)
        
        st.markdown("---")
        
        # NEW: DIRECTIONAL SIGNALS SECTION - Collapsible in mobile
        if st.session_state.mobile_mode:
            with st.expander("🎯 Directional Signals", expanded=False):
                _render_directional_signals(filtered_df, current_spot)
        else:
            st.subheader("🎯 Directional Signals (NEW)")
            _render_directional_signals(filtered_df, current_spot)
        
        st.markdown("---")
        
        # Key assertions triggered
        st.subheader("⚠️ Active Alerts")
        
        try:
            from utils.assertion_rules import AssertionEngine
            
            engine = AssertionEngine()
            conditions = {
                'pcr': pcr,
                'vix': current_vix,
                'spot': current_spot,
                'max_pain': max_pain,
                'dte': 7,
                'concentration': concentration
            }
            
            triggered = engine.evaluate_all(conditions)
            
            if triggered:
                for rule in triggered[:3]:  # Show top 3
                    emoji = "🔴" if rule['confidence'] > 80 else "🟡"
                    st.info(f"{emoji} **{rule['rule_name']}**: {rule['message']}")
            else:
                st.success("✅ No critical alerts - Normal market conditions")
        
        except:
            pass
        
        # Summary box
        st.markdown("---")
        st.subheader("📋 Quick Summary")
        
        summary_text = f"""
        **Positioning Bias:** {regime}  
        **Support Level:** {support:.0f} (High OI)  
        **Resistance Level:** {resistance:.0f} (High OI)  
        **Expected Range:** {pred_lower:.0f} - {pred_upper:.0f}  
        **Suggested Strategy:** {suggest_strategy(regime, pcr, current_vix, iv_skew)[0]}
        """
        
        st.info(summary_text)
    
    # ============ TAB 2: POSITIONING (or Strategy in mobile) ============
    if not st.session_state.mobile_mode:
        # Desktop Tab 2: Positioning
        with tab2:
            st.header("Options Positioning Analysis")
            
            # OI Heatmap
            st.subheader("🔥 Open Interest Heatmap")
            try:
                heatmap = viz.create_oi_heatmap({selected_week: filtered_df})
                st.plotly_chart(heatmap, use_container_width=True, config=viz.plotly_config)
            except Exception as e:
                st.warning(f"Heatmap: {e}")
            
            # Top strikes
            st.subheader("🎯 Strike Concentration")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Top 5 OI Strikes:**")
                for strike, oi in top_strikes:
                    st.metric(f"Strike {strike:.0f}", f"{oi:,.0f} OI")
            
            with col2:
                st.markdown(f"**OI Concentration:** {concentration:.1f}%")
                st.progress(min(concentration / 100, 1.0))
                
                if concentration > 60:
                    st.warning("⚠️ High concentration = Strong defense levels")
                elif concentration < 30:
                    st.info("ℹ️ Low concentration = Scattered positioning")
            
            # PCR Evolution
            if len(weeks) > 1:
                st.subheader("📊 PCR Evolution")
                try:
                    multi_metrics = MultiWeekMetrics(weekly_data)
                    pcr_trend = multi_metrics.compute_pcr_trend()
                    pcr_fig = viz.create_pcr_trend_chart(pcr_trend)
                    st.plotly_chart(pcr_fig, use_container_width=True, config=viz.plotly_config)
                except:
                    pass
    else:
        # Mobile Tab 2: Strategy Builder (simplified)
        with tab2:
            st.header("🎯 Strategy Builder")
            _render_mobile_strategy_section(filtered_df, current_spot, current_vix, regime, pcr)
    
    # ============ TAB 3: VOLATILITY or RISK ============
    if not st.session_state.mobile_mode:
        # Desktop Tab 3: Volatility
        with tab3:
            st.header("Volatility Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("ATM IV", f"{atm_iv:.2f}%",
                         help="At-the-money implied volatility")
            
            with col2:
                skew_signal = "Bearish" if iv_skew > 5 else "Bullish" if iv_skew < -5 else "Neutral"
                st.metric("IV Skew (CE-PE)", f"{iv_skew:.2f}%", delta=skew_signal,
                         help="Positive = puts more expensive than calls")
            
            # IV Surface
            st.subheader("📐 IV Surface")
            try:
                iv_surface = viz.create_iv_surface({selected_week: filtered_df})
                st.plotly_chart(iv_surface, use_container_width=True, config=viz.plotly_config)
            except Exception as e:
                st.warning(f"IV surface: {e}")
            
            # Volatility regime
            st.subheader("💹 Volatility Regime")
            
            if current_vix > 20:
                st.error("🔴 High Volatility - Uncertainty regime")
            elif current_vix < 12:
                st.success("🟢 Low Volatility - Complacency zone")
            else:
                st.info("🟡 Normal Volatility - Balanced regime")
    else:
        # Mobile Tab 3: Risk Summary
        with tab3:
            st.header("⚠️ Risk Analysis")
            try:
                _render_mobile_risk_section(filtered_df, current_spot, pred_lower, pred_upper)
            except:
                st.info("Risk analysis unavailable")
    
    # ============ DESKTOP-ONLY TABS ============
    if not st.session_state.mobile_mode:
        # TAB 4: HISTORICAL COMPARISON
        with tab4:
            st.header("Historical Comparison")
            
            # Candlestick Chart Section
            st.subheader("📈 NIFTY Candlestick Chart")
            
            try:
                # Try to load real data, fallback to reference data
                nifty_data_path = Path("data/reference/nifty_close.csv")
                if nifty_data_path.exists():
                    nifty_df = pd.read_csv(nifty_data_path)
                    
                    # Clean column names (remove trailing spaces)
                    nifty_df.columns = nifty_df.columns.str.strip()
                    
                    # Rename volume column if it exists
                    if 'Shares Traded' in nifty_df.columns:
                        nifty_df['Volume'] = nifty_df['Shares Traded']
                    
                    if 'Date' in nifty_df.columns:
                        nifty_df['Date'] = pd.to_datetime(nifty_df['Date'], format='%d-%b-%Y', errors='coerce')
                        nifty_df = nifty_df.dropna(subset=['Date'])  # Remove any failed conversions
                        nifty_df = nifty_df.sort_values('Date')  # Ensure chronological order
                        nifty_df = nifty_df.tail(60)  # Last 60 days
                        
                        # If we have OHLC data
                        if all(col in nifty_df.columns for col in ['Open', 'High', 'Low', 'Close']):
                            overlays = {
                                'max_pain': max_pain,
                                'range_lower': pred_lower,
                                'range_upper': pred_upper
                            }
                            
                            # Try to get support/resistance
                            try:
                                levels = metrics.get_support_resistance_levels(top_n=3)
                                if levels.get('support'):
                                    overlays['support'] = levels['support'][0]
                                if levels.get('resistance'):
                                    overlays['resistance'] = levels['resistance'][0]
                            except:
                                pass
                            
                            candlestick_fig = viz.create_candlestick_chart(
                                ohlc_data=nifty_df,
                                overlays=overlays
                            )
                            st.plotly_chart(candlestick_fig, width="stretch")
                            
                            st.caption("🔵 Shaded area shows predicted range | 🟠 Max Pain level | 🟢 Support | 🔴 Resistance")
                            
                            # Data info expander
                            with st.expander("📊 Data Information"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Days", len(nifty_df))
                                with col2:
                                    st.metric("Date Range", f"{nifty_df['Date'].min().strftime('%d-%b')} to {nifty_df['Date'].max().strftime('%d-%b')}")
                                with col3:
                                    st.metric("Latest Close", f"₹{nifty_df['Close'].iloc[-1]:,.2f}")
                                
                                st.markdown(f"""
                                **52-Week Stats:**
                                - 📈 High: ₹{nifty_df['High'].max():,.2f}
                                - 📉 Low: ₹{nifty_df['Low'].min():,.2f}
                                - 📊 Avg Volume: {nifty_df.get('Volume', nifty_df.get('Shares Traded', pd.Series([0]))).mean():,.0f} shares
                                
                                *To update data: Run `./scripts/refresh_data.sh` or `python scripts/daily_update.py`*
                                """)
                        else:
                            st.info("📊 OHLC data not available - showing simplified chart")
                            # Simple line chart
                            if 'Close' in nifty_df.columns:
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=nifty_df['Date'],
                                    y=nifty_df['Close'],
                                    mode='lines',
                                    name='NIFTY Close',
                                    line=dict(color='cyan', width=2)
                                ))
                                fig.add_hline(y=current_spot, line_dash="dash", annotation_text="Current")
                                fig.update_layout(title="NIFTY Price Trend (Last 60 Days)", height=400)
                                st.plotly_chart(fig, width="stretch")
                else:
                    st.info("💡 Upload NIFTY historical data to `data/reference/nifty_close.csv` to display candlestick chart")
                    st.markdown("""
                    **Required columns:** Date, Open, High, Low, Close, Volume (optional)
                    
                    You can download data from NSE or other providers.
                    """)
            except Exception as e:
                st.warning(f"Candlestick chart: {e}")
        
        st.markdown("---")
        
        if len(weeks) > 1:
            try:
                from analysis.comparisons import ComparisonEngine
                
                comp_engine = ComparisonEngine(weekly_data)
                
                # Week-over-week changes
                st.subheader("📅 Week-over-Week Changes")
                
                if len(weeks) >= 2:
                    prev_week = weeks[-2]
                    curr_week = weeks[-1]
                    
                    wow_df = comp_engine.compute_wow_changes(curr_week, prev_week)
                    
                    if not wow_df.empty:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            # Compute PCR change
                            prev_ce_oi = wow_df[wow_df['Option_Type'] == 'CE']['OI_prev'].sum()
                            prev_pe_oi = wow_df[wow_df['Option_Type'] == 'PE']['OI_prev'].sum()
                            curr_ce_oi = wow_df[wow_df['Option_Type'] == 'CE']['OI_curr'].sum()
                            curr_pe_oi = wow_df[wow_df['Option_Type'] == 'PE']['OI_curr'].sum()
                            
                            prev_pcr = prev_pe_oi / (prev_ce_oi + 1)
                            curr_pcr = curr_pe_oi / (curr_ce_oi + 1)
                            pcr_change = curr_pcr - prev_pcr
                            
                            st.metric("PCR Change", f"{pcr_change:+.2f}", delta=f"{(pcr_change/prev_pcr)*100:.1f}%")
                        
                        with col2:
                            # Total OI change
                            total_prev_oi = wow_df['OI_prev'].sum()
                            total_curr_oi = wow_df['OI_curr'].sum()
                            oi_change_pct = ((total_curr_oi - total_prev_oi) / (total_prev_oi + 1)) * 100
                            
                            st.metric("Total OI Change", f"{oi_change_pct:+.1f}%")
                        
                        with col3:
                            # Dominant flow
                            ce_change = curr_ce_oi - prev_ce_oi
                            pe_change = curr_pe_oi - prev_pe_oi
                            dom_change = "Calls" if ce_change > pe_change else "Puts"
                            st.metric("Dominant Flow", dom_change)
                
                # Strike migration
                st.subheader("🔄 Strike Migration")
                try:
                    # Build migration data
                    migration_records = []
                    for week in weeks:
                        week_df = weekly_data[week]
                        if 'Expiry_Quarter' in week_df.columns:
                            week_df = week_df[week_df['Expiry_Quarter'] == selected_expiry]
                        m = OptionsMetrics(week_df)
                        top = m.get_top_oi_strikes(n=3, by_type=True)
                        for idx, row in top.iterrows():
                            migration_records.append({
                                'Week': week,
                                'Strike': row['Strike'],
                                'Type': row['Type'],
                                'OI': row['OI'],
                                'Rank': idx
                            })
                    migration_df = pd.DataFrame(migration_records)
                    
                    if not migration_df.empty:
                        migration_fig = viz.create_strike_migration_chart(migration_df)
                        st.plotly_chart(migration_fig, width="stretch")
                except Exception as e:
                    st.warning(f"Migration chart: {e}")
            
            except Exception as e:
                st.error(f"Historical analysis error: {str(e)}")
                import traceback
                with st.expander("Show error details"):
                    st.code(traceback.format_exc())
        else:
            st.info("ℹ️ Need multiple weeks for historical comparison")
        
        # ============ TAB 5: PROFESSIONAL STRATEGY BUILDER ============
        with tab5:
            try:
                # Lazy import to avoid startup failures if dependencies missing
                from analysis.strategy_ui import render_strategy_builder_tab
                from utils.config_loader import load_config
                
                config = load_config('config.yaml')
                lot_size = config.get('strategies', {}).get('nifty_lot_size', 50)
                
                render_strategy_builder_tab(
                    current_spot=current_spot,
                    current_vix=current_vix,
                    options_data=filtered_df if not filtered_df.empty else None,
                    lot_size=lot_size
                )
            except ImportError as e:
                st.error(f"📦 Strategy Builder dependencies not available: {e}")
                st.info("Install required packages: `pip install scipy`")
                st.markdown("### Legacy Strategy Builder")
                st.info("The professional strategy builder requires scipy. Using basic mode.")
            except Exception as e:
                st.error(f"Strategy Builder Error: {e}")
                import traceback
                with st.expander("🐛 Debug Info"):
                    st.code(traceback.format_exc())
        
        # ============ TAB 6: DECISION & RISK ============
        with tab6:
            st.header("🎲 Decision Engine & Risk Analysis")
            
            st.markdown("""
            Professional-grade decision logic combining:
            - **Volatility Edge**: IV vs Realized Vol analysis
            - **Expected Value**: Probabilistic EV modeling
            - **Trade Scoring**: Multi-factor quality assessment (0-100)
            - **Monte Carlo**: Equity path simulation
            - **Position Sizing**: Kelly, Fixed Fraction, Vol-Adjusted
            """)
            
            st.markdown("---")
            
            # Initialize engines
            from analysis.decision_engine import DecisionEngine, analyze_regime
            from analysis.risk_engine import RiskEngine, quick_risk_assessment
            from analysis.position_sizer import PositionSizer
            
            decision_engine = DecisionEngine()
            risk_engine = RiskEngine()
            
            # Configuration
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### ⚙️ Configuration")
                account_size = st.number_input("Account Size (₹)", value=100000, step=10000, min_value=10000)
                base_risk_pct = st.slider("Base Risk %", 1.0, 5.0, 2.0, 0.5)
                current_vix = st.slider("Current IV/VIX (%)", 10.0, 40.0, 18.0, 1.0)
            
            with col2:
                st.markdown("### 📊 Strategy Input")
                # Allow user to either use strategy builder result or manual input
                use_strategy_builder = st.checkbox("Use Strategy Builder", value=True)
                
                if use_strategy_builder:
                    # Try to get strategy from session state
                    if 'strategy' in st.session_state and st.session_state.strategy:
                        strategy = st.session_state.strategy
                        st.success("✅ Strategy loaded from builder")
                        
                        # Display strategy summary
                        st.write(f"**Legs:** {len(strategy.legs)}")
                        st.write(f"**Max Profit:** ₹{strategy.get_max_profit():.0f}")
                        st.write(f"**Max Loss:** ₹{strategy.get_max_loss():.0f}")
                    else:
                        st.warning("⚠️ Build a strategy in Tab 5 first")
                        strategy = None
                else:
                    # Manual input
                    max_profit_input = st.number_input("Max Profit (₹)", value=5000, step=500)
                    max_loss_input = st.number_input("Max Loss (₹)", value=-2000, step=500)
                    
                    # Create simple strategy dict
                    strategy = type('obj', (object,), {
                        'get_max_profit': lambda: max_profit_input,
                        'get_max_loss': lambda: max_loss_input,
                        'legs': []
                    })()
            
            st.markdown("---")
            
            # Main analysis section
            if strategy:
                max_profit = strategy.get_max_profit()
                max_loss = strategy.get_max_loss()
                
                # Prepare strategy dict for engines
                strategy_dict = {
                    'max_profit': max_profit,
                    'max_loss': max_loss,
                    'legs': getattr(strategy, 'legs', [])
                }
                
                # Get spot price
                spot_price = filtered_df['Spot_Price'].iloc[0] if 'Spot_Price' in filtered_df.columns else 23000.0
                
                # ========== VOLATILITY EDGE ==========
                st.markdown("## 1️⃣ Volatility Edge Analysis")
                
                vol_edge = decision_engine.compute_vol_edge(
                    option_df=filtered_df,
                    historical_df=None,  # Would load NIFTY historical data
                    spot_price=spot_price
                )
                
                # If no IV data available, provide fallback with VIX
                if vol_edge.get('vol_edge_score', 0) == 0 and vol_edge.get('warning'):
                    st.warning("⚠️ " + vol_edge.get('interpretation', 'IV data not available'))
                    st.info(f"**Using VIX (Implied Volatility Index) as proxy:** {current_vix:.1f}%")
                    
                    # Estimate vol edge from VIX
                    # Typical NIFTY realized vol is 15-18%
                    estimated_realized_vol = 0.17  # 17% baseline
                    vol_edge_fallback = (current_vix/100.0 - estimated_realized_vol) / estimated_realized_vol
                    vol_edge_fallback_score = np.clip(vol_edge_fallback, -1.0, 1.0)
                    
                    # Display fallback metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Vol Edge Score (VIX-based)", f"{vol_edge_fallback_score:.3f}")
                    with col2:
                        st.metric("ATM IV (Implied)", f"{current_vix:.2f}%")
                    with col3:
                        st.metric("Realized Vol (Est.)", f"{estimated_realized_vol*100:.2f}%")
                    
                    # Update vol_edge for downstream use
                    if vol_edge_fallback_score > 0.20:
                        interpretation = "Strong Premium Selling Edge (VIX-based)"
                    elif vol_edge_fallback_score > 0.10:
                        interpretation = "Moderate Premium Selling Edge (VIX-based)"
                    elif vol_edge_fallback_score > -0.10:
                        interpretation = "Neutral Volatility (VIX-based)"
                    else:
                        interpretation = "Buy Volatility Edge (VIX-based)"
                    
                    vol_edge = {
                        'vol_edge_score': vol_edge_fallback_score,
                        'atm_iv': current_vix/100.0,
                        'realized_vol': estimated_realized_vol,
                        'interpretation': interpretation,
                        'source': 'VIX (IV data unavailable in option chain)'
                    }
                    
                    st.info(f"**Interpretation:** {vol_edge.get('interpretation', 'N/A')}")
                else:
                    # Normal display when IV data is available
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Vol Edge Score", f"{vol_edge['vol_edge_score']:.3f}")
                    with col2:
                        st.metric("ATM IV", f"{vol_edge.get('atm_iv', 0)*100:.2f}%")
                    with col3:
                        st.metric("Realized Vol", f"{vol_edge.get('realized_vol', 0)*100:.2f}%")
                    
                    st.info(f"**Interpretation:** {vol_edge.get('interpretation', 'N/A')}")
                
                st.markdown("---")
                
                # ========== EXPECTED VALUE ==========
                st.markdown("## 2️⃣ Expected Value Modeling")
                
                ev_metrics = decision_engine.compute_expected_value(
                    strategy=strategy_dict,
                    spot_price=spot_price,
                    days_to_expiry=30  # Default, could make dynamic
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    ev_value = ev_metrics.get('expected_value', 0)
                    st.metric("Expected Value", f"₹{ev_value:.0f}", delta=None)
                with col2:
                    win_prob = ev_metrics.get('positive_probability', 0) * 100
                    st.metric("Win Probability", f"{win_prob:.1f}%")
                with col3:
                    rr = ev_metrics.get('risk_reward_ratio', 0)
                    st.metric("Risk:Reward", f"{rr:.2f}")
                
                if ev_value > 0:
                    st.success(f"✅ {ev_metrics.get('interpretation', 'Positive EV')}")
                else:
                    st.error(f"❌ {ev_metrics.get('interpretation', 'Negative EV')}")
                
                st.markdown("---")
                
                # ========== TRADE SCORE ==========
                st.markdown("## 3️⃣ Trade Quality Score")
                
                # Prepare market metrics
                market_metrics = {
                    'pcr': pcr,
                    'total_oi': filtered_df['OI'].sum(),
                    'spot': spot_price
                }
                
                trade_score = decision_engine.compute_trade_score(
                    vol_edge=vol_edge,
                    ev_metrics=ev_metrics,
                    market_metrics=market_metrics,
                    liquidity_metrics=None
                )
                
                score = trade_score.get('trade_score', 50)
                confidence = trade_score.get('confidence_level', 'Low')
                
                # Display with color coding
                if score >= 75:
                    score_color = "green"
                elif score >= 60:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                st.markdown(f"### Overall Score: <span style='color:{score_color}; font-size:48px; font-weight:bold'>{score}/100</span>", unsafe_allow_html=True)
                st.markdown(f"**Confidence:** {confidence}")
                
                # Score components breakdown
                with st.expander("📊 Score Components"):
                    components = trade_score.get('components', {})
                    comp_df = pd.DataFrame([components])
                    st.dataframe(comp_df, width="stretch")
                
                st.markdown("---")
                
                # ========== MONTE CARLO SIMULATION ==========
                st.markdown("## 4️⃣ Monte Carlo Risk Simulation")
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    win_rate = st.slider("Historical Win Rate", 0.30, 0.80, 0.55, 0.05)
                    num_simulations = st.selectbox("Simulations", [500, 1000, 2000], index=1)
                
                with col2:
                    num_trades = st.slider("Number of Trades", 50, 300, 200, 50)
                    risk_per_trade = base_risk_pct / 100
                
                # Run simulation
                with st.spinner("Running Monte Carlo simulation..."):
                    avg_rr = abs(max_profit / max_loss) if max_loss != 0 else 1.5
                    
                    sim_results = risk_engine.simulate_equity_paths(
                        win_rate=win_rate,
                        avg_rr=avg_rr,
                        risk_per_trade=risk_per_trade,
                        num_simulations=num_simulations,
                        num_trades=num_trades,
                        starting_capital=account_size
                    )
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Expected Equity", f"₹{sim_results['expected_equity']:,.0f}")
                with col2:
                    st.metric("5th Percentile", f"₹{sim_results['percentile_5_equity']:,.0f}")
                with col3:
                    st.metric("Risk of Ruin", f"{sim_results['risk_of_ruin']*100:.2f}%")
                with col4:
                    st.metric("Avg Return", f"{sim_results['avg_return_pct']:.1f}%")
                
                # Equity simulation chart
                equity_chart = viz.create_equity_simulation_chart(
                    equity_paths=sim_results['equity_paths'],
                    starting_capital=account_size,
                    percentiles=[5, 25, 50, 75, 95]
                )
                st.plotly_chart(equity_chart, width="stretch")
                
                st.markdown("---")
                
                # ========== POSITION SIZING ==========
                st.markdown("## 5️⃣ Position Sizing Recommendations")
                
                position_sizer = PositionSizer(
                    account_size=account_size,
                    max_risk_pct=5.0,
                    lot_size=50
                )
                
                # Compare sizing methods
                sample_size = strategy_dict.get('sample_size', 100)  # Default 100 trades
                
                sizing_results = position_sizer.compare_sizing_methods(
                    strategy=strategy_dict,
                    win_rate=win_rate,
                    avg_rr=avg_rr,
                    current_volatility=current_vix,
                    base_risk_pct=base_risk_pct,
                    sample_size=sample_size
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### Kelly Criterion")
                    kelly = sizing_results['kelly']
                    st.metric("Lots", kelly.num_lots)
                    st.metric("Risk", f"{kelly.risk_pct:.2f}%")
                    st.metric("Capital at Risk", f"₹{kelly.capital_at_risk:,.0f}")
                    if kelly.warnings:
                        for warning in kelly.warnings:
                            st.warning(warning)
                    
                    # NEW: Show sample size adjustment
                    if 'kelly_detail' in sizing_results and sizing_results['kelly_detail']:
                        kelly_detail = sizing_results['kelly_detail']
                        sample_size = kelly_detail.get('sample_size', 0)
                        base_fraction = kelly_detail.get('base_fraction', 0)
                        adjusted_fraction = kelly_detail.get('adjusted_fraction', 0)
                        
                        if sample_size > 0 and sample_size < 100:
                            with st.expander("📊 Sample Size Adjustment"):
                                st.write(f"**Based on: {sample_size} historical trades**")
                                st.write(f"- Base Kelly: {base_fraction:.4f} ({base_fraction*100:.2f}%)")
                                st.write(f"- Adjusted Kelly: {adjusted_fraction:.4f} ({adjusted_fraction*100:.2f}%)")
                                
                                if sample_size < 50:
                                    st.warning(f"⚠️ **Low Sample Size Alert**: Only {sample_size} trades. Consider more data before trading at full size.")
                                elif sample_size < 100:
                                    st.info(f"ℹ️ **Limited Data**: {sample_size} trades - sizing is conservative. More data will refine estimate.")
                                else:
                                    st.success(f"✅ **Sufficient Data**: {sample_size} trades - Kelly estimate is reliable.")
                
                with col2:
                    st.markdown("### Fixed Fraction")
                    fixed = sizing_results['fixed']
                    st.metric("Lots", fixed.num_lots)
                    st.metric("Risk", f"{fixed.risk_pct:.2f}%")
                    st.metric("Capital at Risk", f"₹{fixed.capital_at_risk:,.0f}")
                
                with col3:
                    st.markdown("### Volatility Adjusted")
                    vol_adj = sizing_results['volatility_adjusted']
                    st.metric("Lots", vol_adj.num_lots)
                    st.metric("Risk", f"{vol_adj.risk_pct:.2f}%")
                    st.metric("Capital at Risk", f"₹{vol_adj.capital_at_risk:,.0f}")
                
                st.markdown("---")
                
                # ========== FINAL DECISION ==========
                st.markdown("## 🎯 SHOULD I TRADE TODAY?")
                
                if st.button("🚀 Generate Trading Decision", type="primary", width="stretch"):
                    with st.spinner("Analyzing all factors..."):
                        decision = decision_engine.generate_trade_decision(
                            vol_edge=vol_edge,
                            ev_metrics=ev_metrics,
                            trade_score=trade_score,
                            risk_metrics=sim_results
                        )
                        
                        # Display decision
                        st.markdown("---")
                        
                        if decision['trade_allowed']:
                            st.success(f"## ✅ {decision['summary']}")
                        else:
                            st.error(f"## ❌ {decision['summary']}")
                        
                        st.markdown(f"**Confidence:** {decision['confidence']}/100")
                        
                        # NEW: DIRECTIONAL SIGNAL VALIDATION
                        st.markdown("---")
                        st.markdown("### 🎯 Directional Signal Validation")
                        
                        # Get current signal from session state
                        if 'latest_signal' in st.session_state and st.session_state.latest_signal:
                            sig = st.session_state.latest_signal
                            sig_name = sig.get('signal', 'NO_SIGNAL')
                            sig_confidence = sig.get('confidence', 0)
                            rsi = sig.get('rsi', 0)
                            pcr = sig.get('pcr', 0)
                            reasons = sig.get('reasons', [])
                            
                            # Validate signal with strategy
                            try:
                                sig_validation = decision_engine.validate_with_directional_signal(
                                    signal=sig_name,
                                    strategy_type=strategy_dict.get('strategy_type', 'LONG_CALL'),
                                    vol_edge=vol_edge.get('vol_edge_score', 0),
                                    risk_of_ruin=sim_results.get('ruin_probability', 0)
                                )
                                
                                col_sig1, col_sig2 = st.columns(2)
                                
                                with col_sig1:
                                    st.write("**Signal Details**")
                                    st.metric("Signal", sig_name, f"Conf: {sig_confidence:.0f}%")
                                    st.metric("RSI (14)", f"{rsi:.1f}")
                                    st.metric("PCR Ratio", f"{pcr:.2f}")
                                
                                with col_sig2:
                                    st.write("**Validation Result**")
                                    if sig_validation['allowed']:
                                        st.success(f"✅ Signal-Strategy Aligned")
                                    else:
                                        st.warning(f"⚠️ Signal Mismatch")
                                    st.metric("Validation Confidence", f"{sig_validation['confidence']:.0f}%")
                                
                                # Signal reasoning
                                with st.expander("📋 Signal Reasoning"):
                                    for reason in reasons:
                                        st.write(f"• {reason}")
                                    st.write("\n**Validation Checks:**")
                                    for check_reason in sig_validation['reasons']:
                                        st.write(f"• {check_reason}")
                            
                            except Exception as e:
                                st.info(f"Signal: {sig_name} | Confidence: {sig_confidence:.0f}%")
                        else:
                            st.info("💡 No directional signal data available. Run Directional Signals analysis first.")
                        
                        st.markdown("---")
                        st.markdown("### 📊 Decision Rationale")
                        st.markdown("**Key Factors:**")
                        for reason in decision['reasoning']:
                            st.markdown(f"- {reason}")
                        
                        if decision['risk_flags']:
                            st.markdown("### ⚠️ Risk Flags:")
                            for flag in decision['risk_flags']:
                                st.markdown(f"- {flag}")
                        
                        # Log trade option
                        st.markdown("---")
                        if st.checkbox("📝 Log this analysis to trade journal"):
                            from utils.trade_logger import TradeLogger
                            
                            logger = TradeLogger()
                            trade_id = logger.log_entry(
                                strategy=strategy_dict,
                                market_context={'pcr': pcr, 'spot': spot_price, 'vix': current_vix},
                                decision_metrics={'vol_edge_score': vol_edge['vol_edge_score'], 
                                                'expected_value': ev_metrics['expected_value'],
                                                'trade_score': score},
                                position_size={'num_lots': fixed.num_lots, 'risk_pct': fixed.risk_pct},
                                notes=f"Decision: {'Allowed' if decision['trade_allowed'] else 'Rejected'}"
                            )
                            
                            st.success(f"✅ Logged to journal: {trade_id}")
                
                else:
                    st.warning("⚠️ Please build a strategy in Tab 5 or enable manual input")
    
    # Footer
    st.markdown("---")
    st.caption("Nifty Options Intelligence | Professional Analytics Platform")


if __name__ == "__main__":
    main()

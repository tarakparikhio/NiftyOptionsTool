"""
Streamlit Dashboard for Options Positioning Intelligence

A structured analytics dashboard for Nifty 50 options.
Focus: Week-to-week structural changes in positioning and volatility.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

# Import custom modules
from data_loader import OptionsDataLoader
from metrics import OptionsMetrics, MultiWeekMetrics
from visualization import OptionsVisualizer
from insights import InsightsEngine

# Page configuration
st.set_page_config(
    page_title="Nifty Options Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    h1 {
        color: #00D9FF;
    }
    h2 {
        color: #FFD700;
    }
    h3 {
        color: #FF6B6B;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data
def load_data(data_folder: str):
    """Load and cache all weekly data."""
    loader = OptionsDataLoader(data_folder)
    weekly_data = loader.load_all_weeks()
    
    # Add derived columns to all weeks
    for week in weekly_data:
        weekly_data[week] = loader.add_derived_columns(weekly_data[week])
    
    return weekly_data, loader.weeks


def display_severity_badge(severity: str) -> str:
    """Return colored badge based on severity."""
    colors = {
        'CRITICAL': '🔴',
        'WARNING': '🟡',
        'INFO': '🔵'
    }
    return colors.get(severity, '⚪')


def display_signal_badge(signal: str) -> str:
    """Return colored badge based on signal."""
    badges = {
        'BULLISH': '🟢 BULLISH',
        'BEARISH': '🔴 BEARISH',
        'NEUTRAL': '⚪ NEUTRAL'
    }
    return badges.get(signal, '⚪ NEUTRAL')


def main():
    # Title
    st.title("📊 Nifty Options Positioning Intelligence")
    st.markdown("*Decision-oriented analytics for discretionary traders*")
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Data folder path
    default_path = "/Users/tarak/Documents/AIPlayGround/Trading/Options/Monthly"
    data_folder = st.sidebar.text_input("Data Folder Path", value=default_path)
    
    # Load data
    try:
        weekly_data, weeks = load_data(data_folder)
        
        if not weekly_data:
            st.error("❌ No data found in the specified folder!")
            return
        
        st.sidebar.success(f"✅ Loaded {len(weeks)} weeks of data")
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return
    
    # Week selection
    st.sidebar.markdown("### 📅 Week Selection")
    selected_week = st.sidebar.selectbox(
        "Select Week",
        weeks,
        index=len(weeks) - 1  # Default to latest week
    )
    
    # Get available expiries for selected week
    current_df = weekly_data[selected_week]
    available_expiries = sorted(current_df['Expiry_Quarter'].unique())
    
    # Expiry selection
    st.sidebar.markdown("### 📆 Expiry Selection")
    selected_expiry_quarter = st.sidebar.selectbox(
        "Select Expiry Quarter",
        ['All'] + list(available_expiries)
    )
    
    # Filter data based on selection
    if selected_expiry_quarter != 'All':
        display_df = current_df[current_df['Expiry_Quarter'] == selected_expiry_quarter]
        expiry_filter = current_df[current_df['Expiry_Quarter'] == selected_expiry_quarter]['Expiry'].iloc[0] if len(current_df) > 0 else None
    else:
        display_df = current_df
        expiry_filter = None
    
    # Visualization theme
    st.sidebar.markdown("### 🎨 Theme")
    theme = st.sidebar.selectbox(
        "Chart Theme",
        ['plotly_dark', 'plotly', 'seaborn', 'ggplot2']
    )
    
    # Initialize visualizer
    viz = OptionsVisualizer(theme=theme)
    
    # Main content area
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📊 Analysis for Week: {selected_week}")
    
    with col2:
        spot_price = display_df['Spot_Price'].iloc[0] if len(display_df) > 0 else 0
        st.metric("Spot Price", f"{spot_price:,.0f}")
    
    with col3:
        total_oi = display_df['OI'].sum()
        st.metric("Total OI", f"{total_oi:,.0f}")
    
    st.markdown("---")
    
    # Tab interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "🎯 Positioning", 
        "📊 IV Analysis", 
        "🔄 Migration", 
        "💡 Insights"
    ])
    
    # ===== TAB 1: OVERVIEW =====
    with tab1:
        st.header("Market Overview")
        
        # Compute metrics
        metrics = OptionsMetrics(display_df)
        
        # Key metrics summary
        col1, col2, col3, col4 = st.columns(4)
        
        pcr_df = metrics.compute_pcr(by_expiry=False)
        pcr_value = pcr_df['PCR'].iloc[0] if not pcr_df.empty else 0
        
        with col1:
            st.metric("PCR (Put-Call Ratio)", f"{pcr_value:.2f}")
        
        with col2:
            max_pain = metrics.compute_max_pain()
            st.metric("Max Pain", f"{max_pain:,.0f}")
        
        with col3:
            concentration = metrics.compute_oi_concentration()
            st.metric("OI Concentration", f"{concentration['concentration_ratio']:.1f}%")
        
        with col4:
            avg_iv = display_df['IV'].mean()
            st.metric("Avg IV", f"{avg_iv:.2f}%")
        
        st.markdown("---")
        
        # Summary dashboard
        st.subheader("📊 Key Metrics Dashboard")
        metrics_dict = {
            'pcr': pcr_value,
            'total_oi': total_oi,
            'max_pain': max_pain,
            'concentration_ratio': concentration['concentration_ratio'],
            'avg_iv': avg_iv,
            'total_volume': display_df['Volume'].sum()
        }
        fig_summary = viz.create_summary_dashboard(metrics_dict, selected_week)
        st.plotly_chart(fig_summary, use_container_width=True)
        
        # OI Distribution
        st.subheader("📊 OI Distribution: Calls vs Puts")
        fig_dist = viz.create_oi_distribution(display_df, spot_price)
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # ===== TAB 2: POSITIONING =====
    with tab2:
        st.header("Positioning Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔝 Top OI Strikes")
            top_oi = metrics.get_top_oi_strikes(n=5, by_type=True)
            
            # Format the display
            ce_top = top_oi[top_oi['Type'] == 'CE'][['Strike', 'OI', 'OI_Change', 'Volume']]
            pe_top = top_oi[top_oi['Type'] == 'PE'][['Strike', 'OI', 'OI_Change', 'Volume']]
            
            st.markdown("**Call Options (CE)**")
            st.dataframe(ce_top.style.format({
                'Strike': '{:.0f}',
                'OI': '{:,.0f}',
                'OI_Change': '{:,.0f}',
                'Volume': '{:,.0f}'
            }), hide_index=True)
            
            st.markdown("**Put Options (PE)**")
            st.dataframe(pe_top.style.format({
                'Strike': '{:.0f}',
                'OI': '{:,.0f}',
                'OI_Change': '{:,.0f}',
                'Volume': '{:,.0f}'
            }), hide_index=True)
        
        with col2:
            st.subheader("🎯 Support & Resistance")
            levels = metrics.get_support_resistance_levels(top_n=5)
            
            st.markdown("**Resistance Levels (Call OI)**")
            for level in levels['resistance']:
                st.markdown(f"- **{level:,.0f}**")
            
            st.markdown("**Support Levels (Put OI)**")
            for level in levels['support']:
                st.markdown(f"- **{level:,.0f}**")
        
        st.markdown("---")
        
        # OI Change scatter
        st.subheader("📍 OI Change by Strike")
        fig_scatter = viz.create_oi_change_scatter(display_df)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # CE/PE Dominance
        st.subheader("⚖️ CE/PE Dominance")
        dominance = metrics.compute_ce_pe_dominance(by_expiry=False)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            oi_dom = dominance['OI_Dominance'].iloc[0]
            st.metric("OI Dominance", oi_dom, delta=None)
        with col2:
            vol_dom = dominance['Volume_Dominance'].iloc[0]
            st.metric("Volume Dominance", vol_dom, delta=None)
        with col3:
            ce_oi = dominance.get('OI_CE', pd.Series([0])).iloc[0]
            pe_oi = dominance.get('OI_PE', pd.Series([0])).iloc[0]
            st.metric("CE/PE OI Ratio", f"{ce_oi/pe_oi:.2f}" if pe_oi > 0 else "N/A")
    
    # ===== TAB 3: IV ANALYSIS =====
    with tab3:
        st.header("Implied Volatility Analysis")
        
        # IV Skew metrics
        skew = metrics.compute_iv_skew()
        
        if skew:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("ATM IV", f"{skew.get('ATM_IV', 0):.2f}%")
            with col2:
                st.metric("OTM IV", f"{skew.get('OTM_IV', 0):.2f}%")
            with col3:
                st.metric("ITM IV", f"{skew.get('ITM_IV', 0):.2f}%")
            with col4:
                st.metric("ATM-OTM Skew", f"{skew.get('ATM_OTM_Skew', 0):.2f}")
        
        st.markdown("---")
        
        # IV Surface over weeks
        if len(weeks) >= 2:
            st.subheader("📈 IV Surface Evolution")
            
            # Prepare weekly data for IV surface
            if len(weeks) > 2:
                weeks_to_show = st.slider(
                    "Number of weeks to display",
                    min_value=2,
                    max_value=min(len(weeks), 10),
                    value=min(len(weeks), 4)
                )
            else:
                weeks_to_show = len(weeks)  # Use all available weeks
            
            recent_weeks = weeks[-weeks_to_show:]
            week_data_dict = {week: weekly_data[week] for week in recent_weeks}
            
            # Filter by expiry if selected
            if expiry_filter:
                week_data_dict = {
                    week: df[df['Expiry'] == expiry_filter] 
                    for week, df in week_data_dict.items()
                }
            
            fig_iv = viz.create_iv_surface(week_data_dict, expiry=expiry_filter)
            st.plotly_chart(fig_iv, use_container_width=True)
            
            st.info("💡 **Interpretation:** Rising IV indicates increasing uncertainty. Widening skew suggests tail risk hedging.")
    
    # ===== TAB 4: MIGRATION =====
    with tab4:
        st.header("Strike Migration & Trends")
        
        if len(weeks) >= 2:
            # PCR Trend
            st.subheader("📊 PCR Trend Over Weeks")
            multi_metrics = MultiWeekMetrics(weekly_data)
            pcr_trend = multi_metrics.compute_pcr_trend(expiry=expiry_filter)
            
            fig_pcr = viz.create_pcr_trend_chart(pcr_trend)
            st.plotly_chart(fig_pcr, use_container_width=True)
            
            st.markdown("---")
            
            # Strike Migration
            st.subheader("🎯 Top Strike Migration")
            migration_df = multi_metrics.track_strike_migration(top_n=3)
            
            if expiry_filter:
                # Filter migration data by expiry
                filtered_migration = []
                for week in weeks:
                    week_df = weekly_data[week]
                    week_df_filtered = week_df[week_df['Expiry'] == expiry_filter]
                    m = OptionsMetrics(week_df_filtered)
                    top = m.get_top_oi_strikes(n=3, by_type=True)
                    for idx, row in top.iterrows():
                        filtered_migration.append({
                            'Week': week,
                            'Strike': row['Strike'],
                            'Type': row['Type'],
                            'OI': row['OI'],
                            'Rank': idx
                        })
                migration_df = pd.DataFrame(filtered_migration)
            
            fig_migration = viz.create_strike_migration_chart(migration_df)
            st.plotly_chart(fig_migration, use_container_width=True)
            
            st.info("💡 **Interpretation:** Upward migration = Market repricing higher. Downward = Defending lower levels.")
            
            st.markdown("---")
            
            # OI Heatmap
            st.subheader("🔥 OI Change Heatmap")
            
            # Option type selector for heatmap
            heatmap_type = st.radio(
                "Select Option Type for Heatmap",
                ['ALL', 'CE', 'PE'],
                horizontal=True
            )
            
            if len(weeks) > 2:
                weeks_for_heatmap = st.slider(
                    "Weeks to include in heatmap",
                    min_value=2,
                    max_value=len(weeks),
                    value=min(len(weeks), 5),
                    key='heatmap_slider'
                )
            else:
                weeks_for_heatmap = len(weeks)  # Use all available weeks
            
            recent_weeks_heatmap = weeks[-weeks_for_heatmap:]
            week_data_heatmap = {week: weekly_data[week] for week in recent_weeks_heatmap}
            
            fig_heatmap = viz.create_oi_heatmap(
                week_data_heatmap, 
                expiry=expiry_filter, 
                option_type=heatmap_type
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.warning("⚠️ Need at least 2 weeks of data for trend analysis")
    
    # ===== TAB 5: INSIGHTS =====
    with tab5:
        st.header("💡 Positioning Intelligence")
        
        # Generate insights
        engine = InsightsEngine(weekly_data, selected_week)
        insights = engine.generate_all_insights(expiry=expiry_filter)
        
        if insights:
            # Overall verdict
            bullish_count = sum(1 for i in insights if i['signal'] == 'BULLISH')
            bearish_count = sum(1 for i in insights if i['signal'] == 'BEARISH')
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Bullish Signals", bullish_count)
            with col2:
                st.metric("Bearish Signals", bearish_count)
            with col3:
                if bullish_count > bearish_count + 2:
                    verdict = "📈 NET BULLISH"
                    verdict_color = "green"
                elif bearish_count > bullish_count + 2:
                    verdict = "📉 NET BEARISH"
                    verdict_color = "red"
                else:
                    verdict = "↔️ NEUTRAL"
                    verdict_color = "orange"
                st.markdown(f"### :{verdict_color}[{verdict}]")
            
            st.markdown("---")
            
            # Display insights by severity
            critical = [i for i in insights if i['severity'] == 'CRITICAL']
            warnings = [i for i in insights if i['severity'] == 'WARNING']
            infos = [i for i in insights if i['severity'] == 'INFO']
            
            if critical:
                st.subheader("🚨 Critical Alerts")
                for insight in critical:
                    with st.expander(f"{insight['category']} - {display_signal_badge(insight['signal'])}", expanded=True):
                        st.warning(insight['message'])
            
            if warnings:
                st.subheader("⚠️ Important Observations")
                for insight in warnings:
                    with st.expander(f"{insight['category']} - {display_signal_badge(insight['signal'])}", expanded=False):
                        st.info(insight['message'])
            
            if infos:
                st.subheader("ℹ️ Additional Insights")
                for insight in infos:
                    with st.expander(f"{insight['category']} - {display_signal_badge(insight['signal'])}", expanded=False):
                        st.text(insight['message'])
            
            st.markdown("---")
            
            # Full text summary
            with st.expander("📄 View Full Text Summary", expanded=False):
                summary = engine.generate_summary()
                st.code(summary, language=None)
        else:
            st.info("No insights generated for the selected period.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Nifty Options Positioning Intelligence Dashboard</p>
        <p>Built for discretionary traders | Focus: Structural changes, not price prediction</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

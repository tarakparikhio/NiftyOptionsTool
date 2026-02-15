"""
Professional Strategy Builder UI Components for Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Optional

from analysis.strategy_builder_v2 import (
    Strategy, OptionLeg, StrategyMetrics,
    StrikeSuggestionEngine,
    create_iron_condor, create_strangle
)


def render_risk_summary_panel(metrics: StrategyMetrics, strategy_name: str):
    """
    Render comprehensive risk summary panel.
    
    Args:
        metrics: StrategyMetrics object
        strategy_name: Name of the strategy
    """
    st.markdown(f"### 📊 Risk Analysis: {strategy_name}")
    
    # Three-column layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 💰 Profit & Loss")
        
        # Max Profit
        if isinstance(metrics.max_profit, float):
            st.metric(
                "Max Profit",
                f"₹{metrics.max_profit:,.0f}",
                help="Maximum possible profit at expiry"
            )
        else:
            st.metric("Max Profit", metrics.max_profit)
        
        # Max Loss
        if isinstance(metrics.max_loss, float):
            loss_color = "red" if metrics.max_loss < 0 else "green"
            st.metric(
                "Max Loss",
                f"₹{abs(metrics.max_loss):,.0f}",
                delta=f"{loss_color}",
                help="Maximum possible loss at expiry"
            )
        else:
            st.metric("Max Loss", metrics.max_loss)
        
        # Risk/Reward
        st.metric(
            "Risk/Reward",
            f"1:{metrics.risk_reward_ratio:.2f}",
            help="Ratio of max profit to max loss"
        )
    
    with col2:
        st.markdown("#### 🎯 Probability & Breakevens")
        
        # POP
        pop_color = "green" if metrics.pop > 0.5 else "red"
        st.metric(
            "Probability of Profit",
            f"{metrics.pop * 100:.1f}%",
            help="Probability that strategy will be profitable at expiry"
        )
        
        # Breakevens
        if metrics.breakevens:
            st.markdown("**Breakeven Points:**")
            for i, be in enumerate(metrics.breakevens, 1):
                st.text(f"  {i}. ₹{be:,.0f}")
        else:
            st.text("No breakevens")
        
        # Strategy Type
        badge_color = "#28a745" if metrics.strategy_type == "CREDIT" else "#dc3545"
        st.markdown(
            f"<div style='background: {badge_color}; color: white; "
            f"padding: 8px; border-radius: 5px; text-align: center;'>"
            f"<b>{metrics.strategy_type} Strategy</b></div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown("#### 📈 Greeks & Margin")
        
        # Net Delta
        delta_interpretation = "Bullish" if metrics.net_delta > 0 else "Bearish" if metrics.net_delta < 0 else "Neutral"
        st.metric(
            "Net Delta",
            f"{metrics.net_delta:.2f}",
            delta=delta_interpretation,
            help="Net directional exposure"
        )
        
        # Net Theta
        st.metric(
            "Net Theta",
            f"₹{metrics.net_theta:.2f}/day",
            help="Daily time decay (positive = earning theta)"
        )
        
        # Net Vega
        st.metric(
            "Net Vega",
            f"{metrics.net_vega:.2f}",
            help="Sensitivity to 1% IV change"
        )
        
        # Margin
        st.metric(
            "Est. Margin",
            f"₹{metrics.estimated_margin:,.0f}",
            help="Estimated margin requirement"
        )
    
    # Premium Flow Summary
    st.markdown("---")
    st.markdown("#### 💸 Premium Flow")
    
    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        st.metric("Credit Received", f"₹{metrics.net_credit:,.0f}")
    with pcol2:
        st.metric("Debit Paid", f"₹{metrics.net_debit:,.0f}")
    with pcol3:
        net_premium = metrics.net_credit - metrics.net_debit
        net_color = "green" if net_premium > 0 else "red"
        st.metric(
            "Net Premium",
            f"₹{net_premium:,.0f}",
            delta="Credit" if net_premium > 0 else "Debit"
        )


def render_dual_payoff_chart(strategy: Strategy, iv: float, dte: int, current_spot: float):
    """
    Render dual payoff charts (expiry + mark-to-market).
    
    Args:
        strategy: Strategy object
        iv: Implied volatility (decimal)
        dte: Days to expiry
        current_spot: Current spot price
    """
    # Generate spot range
    spot_range = np.linspace(current_spot * 0.85, current_spot * 1.15, 300)
    
    # Calculate payoffs
    payoff_expiry = strategy.compute_payoff_at_expiry(spot_range)
    
    # Calculate mark-to-market (halfway to expiry)
    mtm_dte = max(dte // 2, 1)
    payoff_mtm = np.array([
        strategy.mark_to_market(spot, iv, mtm_dte)
        for spot in spot_range
    ])
    
    # Get breakevens
    breakevens = strategy.calculate_breakevens()
    
    # Create figure
    fig = go.Figure()
    
    # Expiry payoff
    fig.add_trace(go.Scatter(
        x=spot_range,
        y=payoff_expiry,
        name='At Expiry',
        mode='lines',
        line=dict(color='#00d9ff', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 217, 255, 0.1)'
    ))
    
    # Mark-to-market payoff
    fig.add_trace(go.Scatter(
        x=spot_range,
        y=payoff_mtm,
        name=f'MTM (T-{mtm_dte} days)',
        mode='lines',
        line=dict(color='#ffa500', width=2, dash='dash')
    ))
    
    # Current spot
    fig.add_vline(
        x=current_spot,
        line_dash="solid",
        line_color="white",
        line_width=2,
        annotation_text=f"Spot: {current_spot:,.0f}",
        annotation_position="top"
    )
    
    # Breakevens
    for i, be in enumerate(breakevens):
        fig.add_vline(
            x=be,
            line_dash="dot",
            line_color="yellow",
            line_width=1,
            annotation_text=f"BE{i+1}: {be:,.0f}",
            annotation_position="bottom" if i % 2 == 0 else "top"
        )
    
    # Zero line
    fig.add_hline(
        y=0,
        line_dash="solid",
        line_color="gray",
        line_width=1
    )
    
    # Layout
    fig.update_layout(
        title=f"{strategy.name} - Profit/Loss Analysis",
        xaxis_title="Nifty Level",
        yaxis_title="Profit/Loss (₹)",
        height=500,
        hovermode='x unified',
        template='plotly_dark',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_strategy_builder_tab(
    current_spot: float,
    current_vix: float,
    options_data: Optional[pd.DataFrame],
    lot_size: int = 50
):
    """
    Render complete professional strategy builder interface.
    
    Args:
        current_spot: Current Nifty spot price
        current_vix: Current VIX level
        options_data: Options chain data (optional, for strike suggestion)
        lot_size: Contract lot size
    """
    st.header("🏗️ Professional Strategy Builder")
    
    st.markdown("""
    Build and analyze multi-leg options strategies with:
    - **Real Premium Tracking** - Accurate P&L with actual premiums
    - **Probability of Profit** - POP calculation using lognormal distribution
    - **Margin Estimation** - SPAN-like margin requirements
    - **Comprehensive Greeks** - Net Delta, Gamma, Theta, Vega
    - **Dual Payoff Charts** - Expiry + Mark-to-Market visualization
    """)
    
    st.markdown("---")
    
    # Strategy selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        strategy_mode = st.radio(
            "Build Strategy",
            ["Quick Presets", "Custom Multi-Leg"],
            horizontal=True
        )
    
    with col2:
        dte = st.number_input(
            "Days to Expiry",
            min_value=1,
            max_value=90,
            value=7,
            help="Days until option expiration"
        )
        
        iv = st.number_input(
            "ATM IV (%)",
            min_value=5.0,
            max_value=50.0,
            value=float(current_vix),
            step=0.5,
            help="At-the-money implied volatility"
        ) / 100  # Convert to decimal
    
    st.markdown("---")
    
    # Initialize strategy variable
    strategy = None
    
    # === QUICK PRESETS ===
    if strategy_mode == "Quick Presets":
        preset_type = st.selectbox(
            "Select Preset Strategy",
            ["Iron Condor", "Long Strangle", "Long Straddle", "Bull Call Spread", "Bear Put Spread"]
        )
        
        if preset_type == "Iron Condor":
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                wing_width = st.slider("Wing Width", 100, 500, 300, 50)
            with col_b:
                short_distance = st.slider("Short Strike Distance", 100, 500, 200, 50)
            with col_c:
                build_btn = st.button("🔨 Build Iron Condor", type="primary",use_container_width=True)
            
            if build_btn or 'current_strategy' in st.session_state:
                # Calculate strikes
                short_call = round(current_spot + short_distance, -2)
                long_call = short_call + wing_width
                short_put = round(current_spot - short_distance, -2)
                long_put = short_put - wing_width
                
                # Prompt for premiums
                st.markdown("#### Enter Premiums:")
                pcol1, pcol2, pcol3, pcol4 = st.columns(4)
                
                with pcol1:
                    lp_prem = st.number_input(f"Long Put ({long_put})", value=10, min_value=1, key="lp")
                with pcol2:
                    sp_prem = st.number_input(f"Short Put ({short_put})", value=40, min_value=1, key="sp")
                with pcol3:
                    sc_prem = st.number_input(f"Short Call ({short_call})", value=40, min_value=1, key="sc")
                with pcol4:
                    lc_prem = st.number_input(f"Long Call ({long_call})", value=10, min_value=1, key="lc")
                
                # Build strategy
                strategy = Strategy("Iron Condor", current_spot, lot_size)
                strategy.add_leg(OptionLeg('PE', 'BUY', long_put, 'weekly', lp_prem, 1))
                strategy.add_leg(OptionLeg('PE', 'SELL', short_put, 'weekly', sp_prem, 1))
                strategy.add_leg(OptionLeg('CE', 'SELL', short_call, 'weekly', sc_prem, 1))
                strategy.add_leg(OptionLeg('CE', 'BUY', long_call, 'weekly', lc_prem, 1))
                
                st.session_state.current_strategy = strategy
        
        elif preset_type == "Long Strangle":
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                distance = st.slider("Strike Distance from ATM", 100, 800, 300, 50)
            with col_b:
                build_btn = st.button("🔨 Build Strangle", type="primary", use_container_width=True)
            
            if build_btn or 'current_strategy' in st.session_state:
                call_strike = round(current_spot + distance, -2)
                put_strike = round(current_spot - distance, -2)
                
                st.markdown("#### Enter Premiums:")
                pcol1, pcol2 = st.columns(2)
                
                with pcol1:
                    call_prem = st.number_input(f"Call ({call_strike})", value=50, min_value=1, key="call")
                with pcol2:
                    put_prem = st.number_input(f"Put ({put_strike})", value=50, min_value=1, key="put")
                
                strategy = Strategy("Long Strangle", current_spot, lot_size)
                strategy.add_leg(OptionLeg('CE', 'BUY', call_strike, 'weekly', call_prem, 1))
                strategy.add_leg(OptionLeg('PE', 'BUY', put_strike, 'weekly', put_prem, 1))
                
                st.session_state.current_strategy = strategy
        
        elif preset_type == "Long Straddle":
            atm_strike = round(current_spot, -2)
            
            if st.button("🔨 Build Straddle", type="primary"):
                st.markdown("#### Enter Premiums:")
                pcol1, pcol2 = st.columns(2)
                
                with pcol1:
                    call_prem = st.number_input(f"ATM Call ({atm_strike})", value=150, min_value=1, key="atm_call")
                with pcol2:
                    put_prem = st.number_input(f"ATM Put ({atm_strike})", value=150, min_value=1, key="atm_put")
                
                strategy = Strategy("Long Straddle", current_spot, lot_size)
                strategy.add_leg(OptionLeg('CE', 'BUY', atm_strike, 'weekly', call_prem, 1))
                strategy.add_leg(OptionLeg('PE', 'BUY', atm_strike, 'weekly', put_prem, 1))
                
                st.session_state.current_strategy = strategy
    
    # === CUSTOM MULTI-LEG ===
    else:  # Custom Multi-Leg
        st.markdown("### 🔧 Build Custom Strategy")
        
        # Initialize legs in session state
        if 'custom_legs' not in st.session_state:
            st.session_state.custom_legs = []
        
        # Add leg form
        with st.expander("➕ Add a New Leg", expanded=True):
            lcol1, lcol2, lcol3 = st.columns(3)
            
            with lcol1:
                leg_type = st.selectbox("Type", ["CE", "PE"], key="leg_type")
                leg_position = st.selectbox("Position", ["BUY", "SELL"], key="leg_pos")
            
            with lcol2:
                leg_strike = st.number_input("Strike", min_value=10000, max_value=50000, 
                                            value=int(current_spot), step=50, key="leg_strike")
                leg_premium = st.number_input("Premium (₹)", min_value=1, max_value=5000,
                                             value=100, step=10, key="leg_prem")
            
            with lcol3:
                leg_qty = st.number_input("Quantity", min_value=1, max_value=10, 
                                         value=1, key="leg_qty")
                
                if st.button("➕ Add Leg", use_container_width=True):
                    new_leg = OptionLeg(
                        leg_type, leg_position, float(leg_strike),
                        'weekly', float(leg_premium), int(leg_qty)
                    )
                    st.session_state.custom_legs.append(new_leg)
                    st.success(f"Added: {leg_position} {leg_qty}x {leg_type} {leg_strike}")
        
        # Display current legs
        if st.session_state.custom_legs:
            st.markdown("### 📋 Current Legs")
            
            for i, leg in enumerate(st.session_state.custom_legs):
                col_info, col_remove = st.columns([4, 1])
                
                with col_info:
                    st.text(f"{i+1}. {leg.position} {leg.quantity}x {leg.type} {leg.strike:.0f} @ ₹{leg.entry_price}")
                
                with col_remove:
                    if st.button("🗑️", key=f"remove_{i}"):
                        st.session_state.custom_legs.pop(i)
                        st.rerun()
            
            # Build strategy button
            strategy_name = st.text_input("Strategy Name", value="Custom Strategy")
            
            if st.button("🔨 Build Strategy", type="primary"):
                strategy = Strategy(strategy_name, current_spot, lot_size)
                for leg in st.session_state.custom_legs:
                    strategy.add_leg(leg)
                
                st.session_state.current_strategy = strategy
                st.success(f"✅ Built: {strategy_name} with {len(strategy.legs)} legs")
    
    # === ANALYSIS & VISUALIZATION ===
    if 'current_strategy' in st.session_state:
        strategy = st.session_state.current_strategy
        
        st.markdown("---")
        
        # Get comprehensive metrics
        with st.spinner("Calculating metrics..."):
            metrics = strategy.get_comprehensive_metrics(iv=iv, dte=dte)
        
        # Render risk summary panel
        render_risk_summary_panel(metrics, strategy.name)
        
        st.markdown("---")
        
        # Render dual payoff chart
        render_dual_payoff_chart(strategy, iv, dte, current_spot)
        
        # Display leg details
        with st.expander("📝 Strategy Legs Details"):
            legs_df = pd.DataFrame([
                {
                    'Type': leg.type,
                    'Position': leg.position,
                    'Strike': f"₹{leg.strike:,.0f}",
                    'Premium': f"₹{leg.entry_price:.2f}",
                    'Quantity': leg.quantity,
                    'Total': f"₹{leg.entry_price * leg.quantity * lot_size:,.2f}"
                }
                for leg in strategy.legs
            ])
            
            st.dataframe(legs_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("👆 Build a strategy using presets or custom legs to see analysis")

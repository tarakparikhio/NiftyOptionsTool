"""
Visualization Module for Options Analytics Dashboard

Creates decision-oriented visualizations:
- OI Change Heatmaps
- PCR Trend Charts
- IV Surface Snapshots
- OI Distribution Curves
- Strike Migration Charts
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class OptionsVisualizer:
    """
    Creates interactive visualizations for options positioning analysis.
    """
    
    def __init__(self, theme: str = 'plotly_dark'):
        """
        Initialize visualizer with theme.
        
        Args:
            theme: Plotly theme ('plotly_dark', 'plotly', 'seaborn', etc.)
        """
        self.theme = theme
        
    def create_oi_heatmap(self, weekly_data: Dict[str, pd.DataFrame], 
                         expiry: Optional[str] = None,
                         option_type: str = 'ALL') -> go.Figure:
        """
        Create heatmap showing OI changes across weeks and strikes.
        
        Args:
            weekly_data: Dict mapping week names to DataFrames
            expiry: Specific expiry to filter (None for all)
            option_type: 'CE', 'PE', or 'ALL'
            
        Returns:
            Plotly Figure object
        """
        # Prepare data
        weeks = sorted(weekly_data.keys())
        all_data = []
        
        for week in weeks:
            df = weekly_data[week].copy()
            if expiry:
                df = df[df['Expiry'] == expiry]
            if option_type != 'ALL':
                df = df[df['Option_Type'] == option_type]
            
            # Group by strike and sum OI
            strike_oi = df.groupby('Strike')['OI_Change'].sum().reset_index()
            strike_oi['Week'] = week
            all_data.append(strike_oi)
        
        if not all_data:
            return go.Figure()
        
        combined = pd.concat(all_data, ignore_index=True)
        
        # Pivot for heatmap
        heatmap_data = combined.pivot(index='Week', columns='Strike', values='OI_Change')
        heatmap_data = heatmap_data.fillna(0)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn',
            zmid=0,
            text=heatmap_data.values,
            texttemplate='%{text:.0f}',
            textfont={"size": 8},
            colorbar=dict(title="OI Change")
        ))
        
        fig.update_layout(
            title=f'OI Change Heatmap - {option_type} ({expiry or "All Expiries"})',
            xaxis_title='Strike Price',
            yaxis_title='Week',
            template=self.theme,
            height=500,
            xaxis=dict(tickangle=-45)
        )
        
        return fig
    
    def create_pcr_trend_chart(self, pcr_trend: pd.DataFrame) -> go.Figure:
        """
        Create PCR trend chart with regime highlighting.
        
        Args:
            pcr_trend: DataFrame with columns: Week, PCR, PE_OI, CE_OI
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add PCR line
        fig.add_trace(
            go.Scatter(
                x=pcr_trend['Week'],
                y=pcr_trend['PCR'],
                name='PCR',
                mode='lines+markers',
                line=dict(color='cyan', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )
        
        # Add threshold lines
        fig.add_hline(y=1.3, line_dash="dash", line_color="red", 
                     annotation_text="Bearish Threshold (1.3)",
                     annotation_position="right")
        fig.add_hline(y=0.7, line_dash="dash", line_color="green",
                     annotation_text="Bullish Threshold (0.7)",
                     annotation_position="right")
        fig.add_hline(y=1.0, line_dash="dot", line_color="gray",
                     annotation_text="Neutral (1.0)")
        
        # Add OI bars
        fig.add_trace(
            go.Bar(
                x=pcr_trend['Week'],
                y=pcr_trend.get('PE_OI', [0]*len(pcr_trend)),
                name='PE OI',
                marker_color='rgba(255, 100, 100, 0.5)',
                yaxis='y2'
            ),
            secondary_y=True
        )
        
        fig.add_trace(
            go.Bar(
                x=pcr_trend['Week'],
                y=pcr_trend.get('CE_OI', [0]*len(pcr_trend)),
                name='CE OI',
                marker_color='rgba(100, 255, 100, 0.5)',
                yaxis='y2'
            ),
            secondary_y=True
        )
        
        # Update layout
        fig.update_xaxes(title_text="Week")
        fig.update_yaxes(title_text="<b>PCR</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>Total OI</b>", secondary_y=True)
        
        fig.update_layout(
            title='Put-Call Ratio (PCR) Trend Analysis',
            template=self.theme,
            height=500,
            hovermode='x unified',
            barmode='group'
        )
        
        return fig
    
    def create_iv_surface(self, weekly_data: Dict[str, pd.DataFrame],
                         expiry: Optional[str] = None) -> go.Figure:
        """
        Create IV surface showing skew across strikes for multiple weeks.
        
        Args:
            weekly_data: Dict mapping week names to DataFrames
            expiry: Specific expiry to filter
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        weeks = sorted(weekly_data.keys())
        colors = px.colors.qualitative.Set2
        
        for idx, week in enumerate(weeks):
            df = weekly_data[week].copy()
            if expiry:
                df = df[df['Expiry'] == expiry]
            
            # Separate CE and PE
            for opt_type, marker_symbol in [('CE', 'circle'), ('PE', 'square')]:
                df_filtered = df[df['Option_Type'] == opt_type].copy()
                df_filtered = df_filtered.sort_values('Strike')
                
                # Use rolling average to smooth IV
                if len(df_filtered) > 3:
                    df_filtered['IV_smooth'] = df_filtered['IV'].rolling(window=3, center=True).mean()
                else:
                    df_filtered['IV_smooth'] = df_filtered['IV']
                
                fig.add_trace(go.Scatter(
                    x=df_filtered['Strike'],
                    y=df_filtered['IV_smooth'],
                    name=f'{week} - {opt_type}',
                    mode='lines+markers',
                    line=dict(color=colors[idx % len(colors)], dash='solid' if opt_type == 'CE' else 'dash'),
                    marker=dict(symbol=marker_symbol, size=6)
                ))
        
        fig.update_layout(
            title=f'IV Surface Evolution ({expiry or "All Expiries"})',
            xaxis_title='Strike Price',
            yaxis_title='Implied Volatility (%)',
            template=self.theme,
            height=500,
            hovermode='closest',
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        return fig
    
    def create_oi_distribution(self, df: pd.DataFrame, spot_price: Optional[float] = None) -> go.Figure:
        """
        Create OI distribution curve showing CE vs PE by strike.
        
        Args:
            df: DataFrame with option chain data
            spot_price: Current spot price (for reference line)
            
        Returns:
            Plotly Figure object
        """
        # Group by strike and option type
        oi_dist = df.groupby(['Strike', 'Option_Type'])['OI'].sum().reset_index()
        
        ce_data = oi_dist[oi_dist['Option_Type'] == 'CE'].sort_values('Strike')
        pe_data = oi_dist[oi_dist['Option_Type'] == 'PE'].sort_values('Strike')
        
        fig = go.Figure()
        
        # Add CE OI (above axis)
        fig.add_trace(go.Bar(
            x=ce_data['Strike'],
            y=ce_data['OI'],
            name='Call OI',
            marker_color='rgba(100, 255, 100, 0.7)',
            hovertemplate='Strike: %{x}<br>CE OI: %{y:,.0f}<extra></extra>'
        ))
        
        # Add PE OI (below axis - negative values)
        fig.add_trace(go.Bar(
            x=pe_data['Strike'],
            y=-pe_data['OI'],  # Negative for visual separation
            name='Put OI',
            marker_color='rgba(255, 100, 100, 0.7)',
            hovertemplate='Strike: %{x}<br>PE OI: %{y:,.0f}<extra></extra>'
        ))
        
        # Add spot price reference line
        if spot_price:
            fig.add_vline(x=spot_price, line_dash="dash", line_color="yellow",
                         annotation_text=f"Spot: {spot_price:.0f}",
                         annotation_position="top")
        
        fig.update_layout(
            title='OI Distribution: Calls (Top) vs Puts (Bottom)',
            xaxis_title='Strike Price',
            yaxis_title='Open Interest',
            template=self.theme,
            height=500,
            barmode='overlay',
            hovermode='x unified',
            yaxis=dict(
                tickformat=',',
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor='white'
            )
        )
        
        return fig
    
    def create_strike_migration_chart(self, migration_df: pd.DataFrame) -> go.Figure:
        """
        Track top OI strikes over weeks (line chart).
        
        Args:
            migration_df: DataFrame with columns: Week, Strike, Type, OI, Rank
            
        Returns:
            Plotly Figure object
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Call Strikes Migration', 'Put Strikes Migration'),
            vertical_spacing=0.15
        )
        
        # Colors for different ranks
        colors = px.colors.qualitative.Bold
        
        # CE strikes migration
        ce_data = migration_df[migration_df['Type'] == 'CE']
        for rank in sorted(ce_data['Rank'].unique())[:3]:  # Top 3
            rank_data = ce_data[ce_data['Rank'] == rank]
            fig.add_trace(
                go.Scatter(
                    x=rank_data['Week'],
                    y=rank_data['Strike'],
                    name=f'CE Rank {rank+1}',
                    mode='lines+markers',
                    line=dict(color=colors[rank % len(colors)], width=2),
                    marker=dict(size=10)
                ),
                row=1, col=1
            )
        
        # PE strikes migration
        pe_data = migration_df[migration_df['Type'] == 'PE']
        for rank in sorted(pe_data['Rank'].unique())[:3]:  # Top 3
            rank_data = pe_data[pe_data['Rank'] == rank]
            fig.add_trace(
                go.Scatter(
                    x=rank_data['Week'],
                    y=rank_data['Strike'],
                    name=f'PE Rank {rank+1}',
                    mode='lines+markers',
                    line=dict(color=colors[rank % len(colors)], width=2, dash='dash'),
                    marker=dict(size=10, symbol='square')
                ),
                row=2, col=1
            )
        
        fig.update_xaxes(title_text="Week", row=2, col=1)
        fig.update_yaxes(title_text="Strike Price", row=1, col=1)
        fig.update_yaxes(title_text="Strike Price", row=2, col=1)
        
        fig.update_layout(
            title='Strike Migration: Where is Defense Moving?',
            template=self.theme,
            height=700,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    def create_oi_change_scatter(self, df: pd.DataFrame) -> go.Figure:
        """
        Create scatter plot of OI Change vs Strike with size based on Volume.
        
        Args:
            df: DataFrame with option chain data
            
        Returns:
            Plotly Figure object
        """
        # Separate CE and PE
        ce_df = df[df['Option_Type'] == 'CE'].copy()
        pe_df = df[df['Option_Type'] == 'PE'].copy()
        
        fig = go.Figure()
        
        # Add CE scatter
        fig.add_trace(go.Scatter(
            x=ce_df['Strike'],
            y=ce_df['OI_Change'],
            mode='markers',
            name='Calls',
            marker=dict(
                size=ce_df['Volume'] / ce_df['Volume'].max() * 50,  # Size based on volume
                color='green',
                opacity=0.6,
                line=dict(width=1, color='white')
            ),
            text=ce_df.apply(lambda row: f"Strike: {row['Strike']}<br>OI Chg: {row['OI_Change']:.0f}<br>Vol: {row['Volume']:.0f}", axis=1),
            hovertemplate='%{text}<extra></extra>'
        ))
        
        # Add PE scatter
        fig.add_trace(go.Scatter(
            x=pe_df['Strike'],
            y=pe_df['OI_Change'],
            mode='markers',
            name='Puts',
            marker=dict(
                size=pe_df['Volume'] / pe_df['Volume'].max() * 50,
                color='red',
                opacity=0.6,
                line=dict(width=1, color='white')
            ),
            text=pe_df.apply(lambda row: f"Strike: {row['Strike']}<br>OI Chg: {row['OI_Change']:.0f}<br>Vol: {row['Volume']:.0f}", axis=1),
            hovertemplate='%{text}<extra></extra>'
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1)
        
        fig.update_layout(
            title='OI Change by Strike (bubble size = volume)',
            xaxis_title='Strike Price',
            yaxis_title='OI Change',
            template=self.theme,
            height=500,
            hovermode='closest'
        )
        
        return fig
    
    def create_summary_dashboard(self, metrics: Dict, week_name: str) -> go.Figure:
        """
        Create a summary dashboard with key metrics.
        
        Args:
            metrics: Dictionary with computed metrics
            week_name: Name of the week
            
        Returns:
            Plotly Figure with indicator panels
        """
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=('PCR', 'Total OI', 'Max Pain', 'OI Concentration', 'Avg IV', 'Volume'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # PCR indicator
        pcr = metrics.get('pcr', 0)
        pcr_color = "red" if pcr > 1.3 else "green" if pcr < 0.7 else "yellow"
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=pcr,
                title={'text': "PCR"},
                gauge={'axis': {'range': [0, 2]},
                       'bar': {'color': pcr_color},
                       'threshold': {
                           'line': {'color': "white", 'width': 4},
                           'thickness': 0.75,
                           'value': 1.0
                       }},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=1
        )
        
        # Total OI
        total_oi = metrics.get('total_oi', 0)
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=total_oi,
                title={'text': "Total OI"},
                number={'valueformat': ',.0f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=2
        )
        
        # Max Pain
        max_pain = metrics.get('max_pain', 0)
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=max_pain,
                title={'text': "Max Pain Strike"},
                number={'valueformat': ',.0f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=3
        )
        
        # OI Concentration
        concentration = metrics.get('concentration_ratio', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=concentration,
                title={'text': "OI Concentration (%)"},
                gauge={'axis': {'range': [0, 100]},
                       'bar': {'color': "lightblue"}},
                number={'suffix': '%'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=1
        )
        
        # Avg IV
        avg_iv = metrics.get('avg_iv', 0)
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=avg_iv,
                title={'text': "Average IV"},
                number={'suffix': '%', 'valueformat': '.2f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=2
        )
        
        # Total Volume
        total_volume = metrics.get('total_volume', 0)
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=total_volume,
                title={'text': "Total Volume"},
                number={'valueformat': ',.0f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=3
        )
        
        fig.update_layout(
            title=f'Market Summary - {week_name}',
            template=self.theme,
            height=600,
            showlegend=False
        )
        
        return fig
    
    def create_equity_simulation_chart(
        self,
        equity_paths: np.ndarray,
        starting_capital: float = 100000.0,
        percentiles: List[int] = [5, 25, 50, 75, 95]
    ) -> go.Figure:
        """
        Create Monte Carlo equity simulation chart.
        
        Shows percentile bands and sample paths.
        
        Args:
            equity_paths: Array of shape (num_simulations, num_trades+1)
            starting_capital: Starting account size
            percentiles: Percentiles to display
            
        Returns:
            Plotly Figure with equity simulation
        """
        num_simulations, num_trades = equity_paths.shape
        trade_numbers = np.arange(num_trades)
        
        fig = go.Figure()
        
        # Calculate percentile bands
        percentile_data = {}
        for p in percentiles:
            percentile_data[p] = np.percentile(equity_paths, p, axis=0)
        
        # Add percentile bands
        colors = {
            5: 'rgba(255, 0, 0, 0.3)',
            25: 'rgba(255, 165, 0, 0.3)',
            50: 'rgba(255, 255, 0, 0.8)',
            75: 'rgba(0, 255, 0, 0.3)',
            95: 'rgba(0, 255, 0, 0.2)'
        }
        
        # Add 5-95 percentile band (shaded area)
        fig.add_trace(go.Scatter(
            x=trade_numbers,
            y=percentile_data[95],
            mode='lines',
            name='95th Percentile',
            line=dict(color='rgba(0, 255, 0, 0.5)', width=1),
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=trade_numbers,
            y=percentile_data[5],
            mode='lines',
            name='5th Percentile',
            line=dict(color='rgba(255, 0, 0, 0.5)', width=1),
            fill='tonexty',
            fillcolor='rgba(100, 100, 100, 0.2)',
            showlegend=True
        ))
        
        # Add 25-75 percentile band
        fig.add_trace(go.Scatter(
            x=trade_numbers,
            y=percentile_data[75],
            mode='lines',
            name='75th Percentile',
            line=dict(color='rgba(0, 200, 0, 0.7)', width=1.5),
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=trade_numbers,
            y=percentile_data[25],
            mode='lines',
            name='25th Percentile',
            line=dict(color='rgba(255, 100, 0, 0.7)', width=1.5),
            fill='tonexty',
            fillcolor='rgba(150, 150, 150, 0.3)',
            showlegend=True
        ))
        
        # Median line (bold)
        fig.add_trace(go.Scatter(
            x=trade_numbers,
            y=percentile_data[50],
            mode='lines',
            name='Median (50th)',
            line=dict(color='yellow', width=3),
            showlegend=True
        ))
        
        # Add a few sample paths (transparent)
        sample_indices = np.random.choice(num_simulations, size=min(20, num_simulations), replace=False)
        for idx in sample_indices:
            fig.add_trace(go.Scatter(
                x=trade_numbers,
                y=equity_paths[idx],
                mode='lines',
                line=dict(color='rgba(100, 100, 100, 0.1)', width=0.5),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Add starting capital reference line
        fig.add_hline(
            y=starting_capital,
            line_dash="dash",
            line_color="cyan",
            annotation_text="Starting Capital"
        )
        
        fig.update_layout(
            title='Monte Carlo Equity Simulation<br><sub>20 sample paths + percentile bands</sub>',
            xaxis_title='Trade Number',
            yaxis_title='Account Equity (₹)',
            template=self.theme,
            height=500,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        return fig
    
    def create_candlestick_chart(
        self,
        ohlc_data: pd.DataFrame,
        overlays: Optional[Dict[str, Any]] = None,
        indicators: Optional[List[str]] = None
    ) -> go.Figure:
        """
        Create candlestick chart with optional overlays.
        
        Args:
            ohlc_data: DataFrame with Date, Open, High, Low, Close, Volume
            overlays: Optional dict with 'support', 'resistance', 'max_pain', etc.
            indicators: Optional list of indicators to add (e.g., ['SMA20', 'EMA50'])
            
        Returns:
            Plotly Figure with candlestick chart
        """
        if not all(col in ohlc_data.columns for col in ['Open', 'High', 'Low', 'Close']):
            raise ValueError("OHLC data must have Open, High, Low, Close columns")
        
        # Create subplots (candlestick + volume)
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=('NIFTY Price', 'Volume'),
            row_heights=[0.7, 0.3]
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=ohlc_data.index if 'Date' not in ohlc_data.columns else ohlc_data['Date'],
                open=ohlc_data['Open'],
                high=ohlc_data['High'],
                low=ohlc_data['Low'],
                close=ohlc_data['Close'],
                name='NIFTY',
                increasing=dict(line=dict(color='#26a69a', width=1.5), fillcolor='#26a69a'),
                decreasing=dict(line=dict(color='#ef5350', width=1.5), fillcolor='#ef5350')
            ),
            row=1, col=1
        )
        
        # Add overlays if provided
        if overlays:
            x_values = ohlc_data.index if 'Date' not in ohlc_data.columns else ohlc_data['Date']
            
            if 'support' in overlays:
                fig.add_hline(
                    y=overlays['support'],
                    line_dash="dot",
                    line_color="green",
                    annotation_text="Support",
                    row=1, col=1
                )
            
            if 'resistance' in overlays:
                fig.add_hline(
                    y=overlays['resistance'],
                    line_dash="dot",
                    line_color="red",
                    annotation_text="Resistance",
                    row=1, col=1
                )
            
            if 'max_pain' in overlays:
                fig.add_hline(
                    y=overlays['max_pain'],
                    line_dash="dash",
                    line_color="orange",
                    annotation_text="Max Pain",
                    row=1, col=1
                )
            
            if 'range_lower' in overlays and 'range_upper' in overlays:
                # Add expected range band
                fig.add_hrect(
                    y0=overlays['range_lower'],
                    y1=overlays['range_upper'],
                    fillcolor="rgba(100, 100, 255, 0.1)",
                    line_width=0,
                    annotation_text="Expected Range",
                    row=1, col=1
                )
        
        # Add indicators if requested
        if indicators and ohlc_data is not None:
            for indicator in indicators:
                if indicator in ohlc_data.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=ohlc_data.index if 'Date' not in ohlc_data.columns else ohlc_data['Date'],
                            y=ohlc_data[indicator],
                            mode='lines',
                            name=indicator,
                            line=dict(width=1.5)
                        ),
                        row=1, col=1
                    )
        
        # Volume bars (if available)
        if 'Volume' in ohlc_data.columns:
            colors = ['green' if close >= open_price else 'red' 
                     for close, open_price in zip(ohlc_data['Close'], ohlc_data['Open'])]
            
            fig.add_trace(
                go.Bar(
                    x=ohlc_data.index if 'Date' not in ohlc_data.columns else ohlc_data['Date'],
                    y=ohlc_data['Volume'],
                    name='Volume',
                    marker_color=colors,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            title='NIFTY Candlestick Chart',
            template=self.theme,
            height=800,
            xaxis_rangeslider_visible=False,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(
            title_text="Date", 
            row=2, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title_text="Price", 
            row=1, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        fig.update_yaxes(
            title_text="Volume", 
            row=2, col=1,
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128, 128, 128, 0.2)'
        )
        
        return fig
    
    def create_decision_dashboard(
        self,
        vol_edge: Dict[str, Any],
        ev_metrics: Dict[str, Any],
        trade_score: Dict[str, Any],
        risk_metrics: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """
        Create unified decision dashboard showing all key metrics.
        
        Args:
            vol_edge: Volatility edge analysis
            ev_metrics: Expected value metrics
            trade_score: Trade quality score
            risk_metrics: Optional risk of ruin metrics
            
        Returns:
            Plotly Figure with decision dashboard
        """
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                'Vol Edge Score',
                'Expected Value',
                'Trade Score',
                'Win Probability',
                'Risk:Reward',
                'Risk of Ruin'
            ),
            specs=[[{'type': 'indicator'}] * 3, 
                   [{'type': 'indicator'}] * 3]
        )
        
        # Vol Edge indicator
        vol_edge_score = vol_edge.get('vol_edge_score', 0)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=vol_edge_score * 100,
                title={'text': "Vol Edge (%)"},
                delta={'reference': 0},
                gauge={
                    'axis': {'range': [-100, 100]},
                    'bar': {'color': 'lightblue'},
                    'steps': [
                        {'range': [-100, -20], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [-20, 20], 'color': 'rgba(255, 255, 0, 0.3)'},
                        {'range': [20, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
                    ],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 15}
                }
            ),
            row=1, col=1
        )
        
        # Expected Value
        ev = ev_metrics.get('expected_value', 0)
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=ev,
                title={'text': "Expected Value (₹)"},
                delta={'reference': 0, 'relative': False},
                number={'prefix': "₹"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=1, col=2
        )
        
        # Trade Score
        score = trade_score.get('trade_score', 50)
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=score,
                title={'text': "Trade Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': 'yellow'},
                    'steps': [
                        {'range': [0, 40], 'color': 'rgba(255, 0, 0, 0.3)'},
                        {'range': [40, 60], 'color': 'rgba(255, 255, 0, 0.3)'},
                        {'range': [60, 100], 'color': 'rgba(0, 255, 0, 0.3)'}
                    ]
                }
            ),
            row=1, col=3
        )
        
        # Win Probability
        win_prob = ev_metrics.get('positive_probability', 0.5) * 100
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=win_prob,
                title={'text': "Win Probability"},
                number={'suffix': "%"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=1
        )
        
        # Risk:Reward
        rr = ev_metrics.get('risk_reward_ratio', 0)
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=rr,
                title={'text': "Risk:Reward"},
                number={'valueformat': '.2f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=2
        )
        
        # Risk of Ruin
        if risk_metrics:
            ror = risk_metrics.get('risk_of_ruin', 0) * 100
        else:
            ror = 0
        
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=ror,
                title={'text': "Risk of Ruin"},
                number={'suffix': "%", 'valueformat': '.2f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=3
        )
        
        fig.update_layout(
            title='Decision Dashboard',
            template=self.theme,
            height=600
        )
        
        return fig


if __name__ == "__main__":
    # Test visualizations
    from data_loader import OptionsDataLoader
    from metrics import OptionsMetrics, MultiWeekMetrics
    
    loader = OptionsDataLoader("/Users/tarak/Documents/AIPlayGround/Trading/Options/Monthly")
    weekly_data_dict = loader.load_all_weeks()
    
    if weekly_data_dict:
        viz = OptionsVisualizer()
        
        # Test PCR trend
        multi_metrics = MultiWeekMetrics(weekly_data_dict)
        pcr_trend = multi_metrics.compute_pcr_trend()
        fig = viz.create_pcr_trend_chart(pcr_trend)
        fig.show()
        
        print("Visualizations created successfully!")

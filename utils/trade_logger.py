"""
Trade Logger - Structured trade journaling for future ML learning
Logs complete trade context, decisions, and outcomes
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class TradeLogger:
    """
    Structured trade journal system.
    
    Logs:
    - Market context (PCR, VIX, regime)
    - Strategy details
    - Decision metrics (vol edge, EV, trade score)
    - Position size and risk
    - Entry/exit prices
    - Outcome (P&L, actual vs expected)
    
    Future use: ML model training on what works
    """
    
    def __init__(self, log_dir: str = "data/trade_logs"):
        """
        Initialize Trade Logger.
        
        Args:
            log_dir: Directory to store trade logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current year log file
        self.log_file = self.log_dir / f"trades_{datetime.now().year}.jsonl"
    
    def log_trade(
        self,
        trade_snapshot: Dict[str, Any],
        stage: str = "entry"
    ) -> str:
        """
        Log a trade entry or exit.
        
        Args:
            trade_snapshot: Complete trade context
            stage: "entry", "exit", or "adjustment"
            
        Returns:
            trade_id for future reference
        """
        # Generate trade ID
        trade_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{stage}"
        
        # Construct log entry
        log_entry = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            **trade_snapshot
        }
        
        # Append to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return trade_id
    
    def log_entry(
        self,
        strategy: Dict[str, Any],
        market_context: Dict[str, Any],
        decision_metrics: Dict[str, Any],
        position_size: Dict[str, Any],
        notes: Optional[str] = None
    ) -> str:
        """
        Log trade entry with complete context.
        
        Args:
            strategy: Strategy details (legs, payoff, Greeks)
            market_context: PCR, VIX, spot, regime
            decision_metrics: Vol edge, EV, trade score
            position_size: Recommended size, lots, risk %
            notes: Optional trader notes
            
        Returns:
            trade_id
        """
        snapshot = {
            'strategy': strategy,
            'market_context': market_context,
            'decision_metrics': decision_metrics,
            'position_size': position_size,
            'notes': notes,
            'entry_time': datetime.now().isoformat()
        }
        
        return self.log_trade(snapshot, stage="entry")
    
    def log_exit(
        self,
        trade_id: str,
        exit_price: float,
        actual_pnl: float,
        exit_reason: str,
        hold_duration_days: Optional[int] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Log trade exit and outcome.
        
        Args:
            trade_id: Original trade ID from entry
            exit_price: Exit price
            actual_pnl: Realized P&L
            exit_reason: "target", "stop", "expiry", "manual"
            hold_duration_days: Days held
            notes: Optional exit notes
            
        Returns:
            exit_log_id
        """
        snapshot = {
            'original_trade_id': trade_id,
            'exit_price': exit_price,
            'actual_pnl': actual_pnl,
            'exit_reason': exit_reason,
            'hold_duration_days': hold_duration_days,
            'notes': notes,
            'exit_time': datetime.now().isoformat()
        }
        
        return self.log_trade(snapshot, stage="exit")
    
    def load_trades(
        self,
        year: Optional[int] = None,
        stage: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load trades from log file.
        
        Args:
            year: Optional year filter
            stage: Optional stage filter ("entry", "exit")
            
        Returns:
            DataFrame of trades
        """
        if year is None:
            year = datetime.now().year
        
        log_file = self.log_dir / f"trades_{year}.jsonl"
        
        if not log_file.exists():
            return pd.DataFrame()
        
        # Read JSONL
        trades = []
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    trades.append(json.loads(line))
        
        if not trades:
            return pd.DataFrame()
        
        df = pd.DataFrame(trades)
        
        # Filter by stage if requested
        if stage:
            df = df[df['stage'] == stage]
        
        return df
    
    def get_trade_summary(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate summary statistics for logged trades.
        
        Args:
            year: Optional year filter
            
        Returns:
            dict with summary metrics
        """
        entries = self.load_trades(year=year, stage="entry")
        exits = self.load_trades(year=year, stage="exit")
        
        if entries.empty:
            return {
                'total_trades': 0,
                'error': 'No trades logged'
            }
        
        # Match entries with exits
        closed_trades = []
        for _, exit_row in exits.iterrows():
            original_id = exit_row.get('original_trade_id')
            if original_id:
                # Find matching entry
                entry = entries[entries['trade_id'] == original_id]
                if not entry.empty:
                    closed_trades.append({
                        'entry': entry.iloc[0].to_dict(),
                        'exit': exit_row.to_dict()
                    })
        
        # Calculate metrics
        total_entries = len(entries)
        total_exits = len(exits)
        closed_count = len(closed_trades)
        open_count = total_entries - closed_count
        
        # P&L analysis for closed trades
        if closed_trades:
            pnls = [t['exit']['actual_pnl'] for t in closed_trades]
            wins = [p for p in pnls if p > 0]
            losses = [p for p in pnls if p < 0]
            
            win_rate = len(wins) / len(pnls) if pnls else 0
            avg_win = sum(wins) / len(wins) if wins else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            expectancy = sum(pnls) / len(pnls)
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            expectancy = 0
        
        return {
            'total_trades': total_entries,
            'open_trades': open_count,
            'closed_trades': closed_count,
            'win_rate': round(win_rate, 3),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'expectancy': round(expectancy, 2),
            'total_pnl': round(sum(pnls) if closed_trades else 0, 2)
        }
    
    def export_for_analysis(
        self,
        year: Optional[int] = None,
        output_file: Optional[str] = None
    ) -> str:
        """
        Export trades to CSV for external analysis.
        
        Args:
            year: Optional year filter
            output_file: Optional output path
            
        Returns:
            Path to exported file
        """
        entries = self.load_trades(year=year, stage="entry")
        
        if entries.empty:
            raise ValueError("No trades to export")
        
        # Flatten nested dicts for CSV
        flattened = []
        for _, row in entries.iterrows():
            flat_row = {
                'trade_id': row['trade_id'],
                'timestamp': row['timestamp'],
                'stage': row['stage']
            }
            
            # Extract key fields from nested structures
            if 'market_context' in row and isinstance(row['market_context'], dict):
                flat_row['pcr'] = row['market_context'].get('pcr')
                flat_row['spot'] = row['market_context'].get('spot')
                flat_row['vix'] = row['market_context'].get('vix')
            
            if 'decision_metrics' in row and isinstance(row['decision_metrics'], dict):
                flat_row['trade_score'] = row['decision_metrics'].get('trade_score')
                flat_row['vol_edge'] = row['decision_metrics'].get('vol_edge_score')
                flat_row['expected_value'] = row['decision_metrics'].get('expected_value')
            
            if 'position_size' in row and isinstance(row['position_size'], dict):
                flat_row['num_lots'] = row['position_size'].get('num_lots')
                flat_row['risk_pct'] = row['position_size'].get('risk_pct')
            
            flattened.append(flat_row)
        
        df = pd.DataFrame(flattened)
        
        # Output file
        if output_file is None:
            output_file = self.log_dir / f"trades_{year or datetime.now().year}_export.csv"
        else:
            output_file = Path(output_file)
        
        df.to_csv(output_file, index=False)
        
        return str(output_file)
    
    def analyze_patterns(self, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze patterns in trade history.
        
        Useful for identifying:
        - Which strategies work best
        - Optimal market conditions
        - Win rate by regime
        
        Args:
            year: Optional year filter
            
        Returns:
            dict with pattern analysis
        """
        entries = self.load_trades(year=year, stage="entry")
        exits = self.load_trades(year=year, stage="exit")
        
        if entries.empty:
            return {'error': 'No data to analyze'}
        
        patterns = {}
        
        # Match entries with exits
        closed_trades = []
        for _, exit_row in exits.iterrows():
            original_id = exit_row.get('original_trade_id')
            if original_id:
                entry = entries[entries['trade_id'] == original_id]
                if not entry.empty:
                    closed_trades.append({
                        'entry': entry.iloc[0].to_dict(),
                        'exit': exit_row.to_dict(),
                        'pnl': exit_row['actual_pnl']
                    })
        
        if not closed_trades:
            return {'error': 'No closed trades to analyze'}
        
        # Pattern 1: Win rate by trade score
        score_brackets = {
            'high_score': [t for t in closed_trades 
                          if t['entry'].get('decision_metrics', {}).get('trade_score', 0) >= 75],
            'med_score': [t for t in closed_trades 
                         if 60 <= t['entry'].get('decision_metrics', {}).get('trade_score', 0) < 75],
            'low_score': [t for t in closed_trades 
                         if t['entry'].get('decision_metrics', {}).get('trade_score', 0) < 60]
        }
        
        patterns['by_trade_score'] = {}
        for bracket, trades in score_brackets.items():
            if trades:
                wins = sum(1 for t in trades if t['pnl'] > 0)
                patterns['by_trade_score'][bracket] = {
                    'win_rate': round(wins / len(trades), 3),
                    'count': len(trades),
                    'avg_pnl': round(sum(t['pnl'] for t in trades) / len(trades), 2)
                }
        
        # Pattern 2: Best performing vol edge range
        vol_edge_brackets = {
            'high_vol_edge': [t for t in closed_trades 
                             if t['entry'].get('decision_metrics', {}).get('vol_edge_score', 0) > 0.2],
            'med_vol_edge': [t for t in closed_trades 
                            if 0 <= t['entry'].get('decision_metrics', {}).get('vol_edge_score', 0) <= 0.2],
            'neg_vol_edge': [t for t in closed_trades 
                            if t['entry'].get('decision_metrics', {}).get('vol_edge_score', 0) < 0]
        }
        
        patterns['by_vol_edge'] = {}
        for bracket, trades in vol_edge_brackets.items():
            if trades:
                wins = sum(1 for t in trades if t['pnl'] > 0)
                patterns['by_vol_edge'][bracket] = {
                    'win_rate': round(wins / len(trades), 3),
                    'count': len(trades),
                    'avg_pnl': round(sum(t['pnl'] for t in trades) / len(trades), 2)
                }
        
        return patterns


# Utility functions

def quick_log_entry(
    strategy_name: str,
    pcr: float,
    spot: float,
    trade_score: int,
    num_lots: int,
    notes: str = ""
) -> str:
    """
    Quick trade entry logging.
    
    Args:
        strategy_name: Name of strategy
        pcr: Put-Call Ratio
        spot: NIFTY spot price
        trade_score: Trade quality score
        num_lots: Number of lots
        notes: Optional notes
        
    Returns:
        trade_id
    """
    logger = TradeLogger()
    
    snapshot = {
        'strategy': {'name': strategy_name},
        'market_context': {'pcr': pcr, 'spot': spot},
        'decision_metrics': {'trade_score': trade_score},
        'position_size': {'num_lots': num_lots},
        'notes': notes
    }
    
    return logger.log_trade(snapshot, stage="entry")


def create_sample_log():
    """Create sample trade log for testing"""
    logger = TradeLogger()
    
    # Sample entry
    logger.log_entry(
        strategy={
            'name': 'Iron Condor',
            'legs': [
                {'type': 'SELL', 'strike': 23000, 'option_type': 'CE'},
                {'type': 'BUY', 'strike': 23200, 'option_type': 'CE'},
                {'type': 'SELL', 'strike': 22800, 'option_type': 'PE'},
                {'type': 'BUY', 'strike': 22600, 'option_type': 'PE'}
            ],
            'max_profit': 8000,
            'max_loss': 2000
        },
        market_context={
            'pcr': 1.15,
            'spot': 22900,
            'vix': 16.5,
            'regime': 'Moderate Fear'
        },
        decision_metrics={
            'vol_edge_score': 0.18,
            'expected_value': 1200,
            'trade_score': 78,
            'confidence': 'High'
        },
        position_size={
            'num_lots': 2,
            'risk_pct': 2.5,
            'capital_at_risk': 4000
        },
        notes="High conviction setup, market showing fear"
    )
    
    print("Sample trade log created in data/trade_logs/")

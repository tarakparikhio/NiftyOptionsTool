"""
Trader Assertion Rules Engine

Configurable rule-based system for detecting market regimes and conditions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional


class AssertionRule:
    """Single assertion rule with condition and trigger."""
    
    def __init__(self, name: str, description: str, 
                 condition_func, threshold: Dict, output_format: str):
        """
        Initialize assertion rule.
        
        Args:
            name: Rule name
            description: What the rule detects
            condition_func: Function that evaluates the condition
            threshold: Dictionary of threshold values
            output_format: Format string for output
        """
        self.name = name
        self.description = description
        self.condition_func = condition_func
        self.threshold = threshold
        self.output_format = output_format
    
    def evaluate(self, data: Dict) -> Optional[Dict]:
        """
        Evaluate the rule against data.
        
        Args:
            data: Dictionary with metrics
            
        Returns:
            Result dictionary if rule triggers, None otherwise
        """
        try:
            trigger_value, confidence = self.condition_func(data, self.threshold)
            
            if trigger_value is not None:
                return {
                    'rule_name': self.name,
                    'description': self.description,
                    'trigger_value': trigger_value,
                    'threshold': self.threshold,
                    'confidence': confidence,
                    'message': self.output_format.format(**data, trigger_value=trigger_value)
                }
        except Exception as e:
            pass
        
        return None


class AssertionEngine:
    """
    Engine for evaluating all assertion rules.
    """
    
    def __init__(self):
        """Initialize with default rules."""
        self.rules = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default trading assertion rules."""
        
        # Rule 1: High PCR + High VIX
        self.add_rule(
            name="VolatilityExpansion",
            description="High PCR + High VIX indicates volatility regime expanding",
            condition_func=lambda d, t: (
                (d['pcr'], 85) if d.get('pcr', 0) > t['pcr'] and d.get('vix', 0) > t['vix'] 
                else (None, 0)
            ),
            threshold={'pcr': 1.3, 'vix': 18},
            output_format="⚠️ Volatility Expansion: PCR={pcr:.2f} (>{threshold[pcr]}), VIX={vix:.2f} (>{threshold[vix]})"
        )
        
        # Rule 2: OI Shift Upward
        self.add_rule(
            name="BullishPositioning",
            description="OI shift upwards for 3+ periods indicates bullish positioning",
            condition_func=lambda d, t: (
                (d.get('periods_up', 0), 80) if d.get('periods_up', 0) >= t['periods'] 
                else (None, 0)
            ),
            threshold={'periods': 3},
            output_format="📈 Bullish Positioning: Strikes migrating UP for {trigger_value} periods"
        )
        
        # Rule 3: Large PE OI Unwinding
        self.add_rule(
            name="BearishHedgeCover",
            description="Large unwinding of OTM PE OI indicates bearish hedge cover",
            condition_func=lambda d, t: (
                (d.get('pe_oi_change', 0), 75) if d.get('pe_oi_change', 0) < -t['threshold'] 
                else (None, 0)
            ),
            threshold={'threshold': 100000},
            output_format="⚠️ Bearish Hedge Cover: PE OI dropped by {trigger_value:,.0f}"
        )
        
        # Rule 4: Daily IV Jump + Falling Underlying
        self.add_rule(
            name="PanicRegime",
            description="Daily IV jump + falling underlying indicates panic regime",
            condition_func=lambda d, t: (
                (d.get('iv_change', 0), 90) 
                if d.get('iv_change', 0) > t['iv_jump'] and d.get('spot_change', 0) < -t['spot_drop'] 
                else (None, 0)
            ),
            threshold={'iv_jump': 15, 'spot_drop': 1},
            output_format="🚨 Panic Regime: IV +{iv_change:.1f}%, Spot -{spot_change:.1f}%"
        )
        
        # Rule 5: Extreme Low VIX
        self.add_rule(
            name="Complacency",
            description="Extremely low VIX indicates market complacency",
            condition_func=lambda d, t: (
                (d.get('vix', 0), 70) if d.get('vix', 100) < t['vix'] 
                else (None, 0)
            ),
            threshold={'vix': 11},
            output_format="😌 Complacency Alert: VIX at {vix:.2f} (very low)"
        )
        
        # Rule 6: High OI Concentration at Key Level
        self.add_rule(
            name="StrongDefense",
            description="High OI concentration at key levels indicates strong defense",
            condition_func=lambda d, t: (
                (d.get('concentration', 0), 75) if d.get('concentration', 0) > t['concentration'] 
                else (None, 0)
            ),
            threshold={'concentration': 50},
            output_format="🛡️ Strong Defense: {concentration:.1f}% OI at top strikes"
        )
        
        # Rule 7: Split Market (CE vs PE divergence)
        self.add_rule(
            name="MarketUncertainty",
            description="CE building up while PE also building indicates uncertainty",
            condition_func=lambda d, t: (
                (abs(d.get('ce_change', 0) - d.get('pe_change', 0)), 70)
                if d.get('ce_change', 0) > t['threshold'] and d.get('pe_change', 0) > t['threshold']
                else (None, 0)
            ),
            threshold={'threshold': 50000},
            output_format="⚖️ Market Uncertainty: Both CE and PE building (CE:{ce_change:,.0f}, PE:{pe_change:,.0f})"
        )
        
        # Rule 8: Max Pain Far from Spot
        self.add_rule(
            name="ExpiryPull",
            description="Max Pain far from spot with low DTE indicates strong gravitational pull",
            condition_func=lambda d, t: (
                (abs(d.get('max_pain', d.get('spot', 0)) - d.get('spot', 0)), 75)
                if abs(d.get('max_pain', d.get('spot', 0)) - d.get('spot', 0)) > t['distance'] 
                and d.get('dte', 999) < t['dte']
                else (None, 0)
            ),
            threshold={'distance': 300, 'dte': 5},
            output_format="🧲 Expiry Pull: Max Pain at {max_pain:.0f}, Spot at {spot:.0f}, DTE: {dte}"
        )
    
    def add_rule(self, name: str, description: str, condition_func, 
                 threshold: Dict, output_format: str):
        """Add a custom rule to the engine."""
        rule = AssertionRule(name, description, condition_func, threshold, output_format)
        self.rules.append(rule)
    
    def evaluate_all(self, data: Dict) -> List[Dict]:
        """
        Evaluate all rules against data.
        
        Args:
            data: Dictionary with all metrics
            
        Returns:
            List of triggered rules
        """
        triggered = []
        
        for rule in self.rules:
            result = rule.evaluate(data)
            if result:
                triggered.append(result)
        
        return triggered
    
    def get_report(self, data: Dict) -> str:
        """
        Generate formatted assertion report.
        
        Args:
            data: Dictionary with metrics
            
        Returns:
            Formatted string
        """
        triggered = self.evaluate_all(data)
        
        if not triggered:
            return "\n✅ No assertion rules triggered. Normal market conditions.\n"
        
        report = ["\n" + "="*70]
        report.append("ASSERTION RULES TRIGGERED")
        report.append("="*70)
        
        # Sort by confidence
        triggered.sort(key=lambda x: x['confidence'], reverse=True)
        
        for i, rule in enumerate(triggered, 1):
            report.append(f"\n[{i}] {rule['rule_name']} (Confidence: {rule['confidence']}%)")
            report.append(f"    {rule['description']}")
            report.append(f"    {rule['message']}")
        
        report.append("\n" + "="*70)
        report.append(f"Total Rules Triggered: {len(triggered)}")
        report.append("="*70 + "\n")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Test assertion engine
    engine = AssertionEngine()
    
    # Sample data
    test_data = {
        'pcr': 1.45,
        'vix': 19.5,
        'spot': 26000,
        'max_pain': 26500,
        'dte': 3,
        'concentration': 55,
        'iv_change': 8,
        'spot_change': -0.5,
        'ce_change': 85000,
        'pe_change': 120000,
        'periods_up': 3
    }
    
    print(engine.get_report(test_data))

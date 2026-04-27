import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.app.drift.compute import compute_metrics, run_hourly_drift_check

def test_drift_detection_flow():
    # Synthetic 30-day stream, 200 decisions/day.
    # Days 1-14 fair, days 15-30 inject 20% approval-rate drop on protected group.
    np.random.seed(42)
    rows = []
    start_date = datetime(2025, 1, 1)
    
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        for _ in range(200):
            group = np.random.choice([0, 1]) # 0: privileged, 1: protected
            outcome = np.random.choice([0, 1])
            
            # Base approval rate: 80% for high outcome, 20% for low outcome
            rate = 0.8 if outcome == 1 else 0.2
            
            # Inject 20% drop for protected group after day 14
            if day >= 14 and group == 1:
                rate *= 0.8
                
            decision = 1 if np.random.rand() < rate else 0
            rows.append({
                "audit_id": "audit-123",
                "timestamp": current_date,
                "protected_attrs": {"group": group},
                "decision": decision,
                "outcome": outcome
            })
            
    # Baseline computed from first 14 days (simplified)
    # In real app, baseline is fixed at audit time.
    baseline = {
        "dp_mean": 0.0,
        "dp_std": 0.02,
        "eo_mean": 0.0,
        "eo_std": 0.02
    }
    
    # Test day 10 (should be fair)
    day10_rows = [r for r in rows if r["timestamp"] <= start_date + timedelta(days=10)]
    res_fair = run_hourly_drift_check("audit-123", day10_rows, baseline)
    assert not res_fair["alert_fired"]
    
    # Test day 20 (should detect drift)
    day20_rows = [r for r in rows if r["timestamp"] <= start_date + timedelta(days=20)]
    res_drift = run_hourly_drift_check("audit-123", day20_rows, baseline)
    assert res_drift["alert_fired"]
    assert res_drift["impact_ratio"] < 0.85

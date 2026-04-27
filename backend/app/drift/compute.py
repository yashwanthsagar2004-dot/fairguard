import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def compute_metrics(df, protected_key):
    if df.empty: return 0.0, 0.0, 1.0
    
    groups = df["protected_attrs"].apply(lambda x: x.get(protected_key, 0))
    priv = (groups == 0)
    prot = (groups == 1)
    
    priv_rate = df[priv]["decision"].mean() if priv.any() else 0.0
    prot_rate = df[prot]["decision"].mean() if prot.any() else 0.0
    
    dp_diff = priv_rate - prot_rate
    ir = (prot_rate / priv_rate) if priv_rate > 0 else 1.0
    
    eo_gap = 0.0
    if "outcome" in df.columns:
        tpr_priv = df[priv & (df["outcome"] == 1)]["decision"].mean() if (priv & (df["outcome"] == 1)).any() else 0.0
        tpr_prot = df[prot & (df["outcome"] == 1)]["decision"].mean() if (prot & (df["outcome"] == 1)).any() else 0.0
        eo_gap = abs(tpr_priv - tpr_prot)
        
    return dp_diff, eo_gap, ir

def run_hourly_drift_check(audit_id, decisions, baseline):
    df = pd.DataFrame(decisions)
    dp, eo, ir = compute_metrics(df, "group")
    
    alert = False
    if abs(dp - baseline["dp_mean"]) > 2 * baseline["dp_std"]: alert = True
    if abs(eo - baseline["eo_mean"]) > 2 * baseline["eo_std"]: alert = True
    if ir < 0.8: alert = True
    
    if alert:
        logger.warning(f"DRIFT ALERT for {audit_id}: DP={dp}, EO={eo}, IR={ir}")
    
    return {
        "audit_id": audit_id,
        "computed_at": datetime.now().isoformat(),
        "demographic_parity_diff": dp,
        "equalized_odds_gap": eo,
        "impact_ratio": ir,
        "alert_fired": alert
    }

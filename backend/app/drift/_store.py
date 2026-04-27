"""
In-memory stores for drift monitoring (dev/test mode).

In production these are replaced by BigQuery reads/writes.
"""

from typing import Any, Dict, List

# Mirrors BigQuery fairguard_monitoring.decisions
decisions_store: List[Dict[str, Any]] = []

# Mirrors BigQuery fairguard_monitoring.drift_metrics
drift_metrics_store: List[Dict[str, Any]] = []

# Active drift-monitor registrations  {audit_id: {webhook_url, email}}
registrations: Dict[str, Dict[str, Any]] = {}

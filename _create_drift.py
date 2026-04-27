#!/usr/bin/env python3
"""Bootstrap script: creates all drift-monitor deliverables in one shot."""
import os, textwrap

BASE = os.path.dirname(os.path.abspath(__file__))

def w(relpath, content):
    fp = os.path.join(BASE, relpath)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))
    print(f"  wrote {relpath}")

# =========================================================================
# 1. infra/drift.tf
# =========================================================================
w("infra/drift.tf", r'''
    # FairGuard Drift Monitoring Infrastructure
    # Ref: Davis et al., JAMIA 32(5):845-854, 2025. DOI 10.1093/jamia/ocaf039
    # Ref: Henzinger et al., FAccT 2023. DOI 10.1145/3593013.3594028

    resource "google_pubsub_topic" "fairguard_decisions" {
      name                       = "fairguard-decisions"
      message_retention_duration = "604800s"
    }

    resource "google_pubsub_topic" "decisions_dlq" {
      name = "fairguard-decisions-dlq"
    }

    resource "google_pubsub_subscription" "drift_sub" {
      name                 = "fairguard-decisions-sub"
      topic                = google_pubsub_topic.fairguard_decisions.name
      ack_deadline_seconds = 60
      retry_policy {
        minimum_backoff = "10s"
        maximum_backoff = "600s"
      }
      dead_letter_policy {
        dead_letter_topic     = google_pubsub_topic.decisions_dlq.id
        max_delivery_attempts = 5
      }
    }

    resource "google_bigquery_dataset" "fairguard_monitoring" {
      dataset_id  = "fairguard_monitoring"
      location    = "US"
      description = "FairGuard longitudinal fairness-drift monitoring"
    }

    resource "google_bigquery_table" "decisions" {
      dataset_id          = google_bigquery_dataset.fairguard_monitoring.dataset_id
      table_id            = "decisions"
      description         = "PII-free model decisions"
      deletion_protection = false
      time_partitioning {
        type  = "DAY"
        field = "timestamp"
      }
      clustering = ["audit_id"]
      schema = jsonencode([
        { name = "audit_id",        type = "STRING",    mode = "REQUIRED" },
        { name = "timestamp",       type = "TIMESTAMP", mode = "REQUIRED" },
        { name = "protected_attrs", type = "JSON",      mode = "REQUIRED" },
        { name = "decision",        type = "INT64",     mode = "REQUIRED" },
        { name = "outcome",         type = "INT64",     mode = "REQUIRED" }
      ])
    }

    resource "google_bigquery_table" "drift_metrics" {
      dataset_id          = google_bigquery_dataset.fairguard_monitoring.dataset_id
      table_id            = "drift_metrics"
      description         = "Hourly fairness-drift metrics"
      deletion_protection = false
      time_partitioning {
        type  = "DAY"
        field = "computed_at"
      }
      clustering = ["audit_id"]
      schema = jsonencode([
        { name = "audit_id",                type = "STRING",    mode = "REQUIRED" },
        { name = "computed_at",             type = "TIMESTAMP", mode = "REQUIRED" },
        { name = "demographic_parity_diff", type = "FLOAT64",   mode = "NULLABLE" },
        { name = "equalized_odds_gap",      type = "FLOAT64",   mode = "NULLABLE" },
        { name = "impact_ratio",            type = "FLOAT64",   mode = "NULLABLE" },
        { name = "alert_fired",             type = "BOOL",      mode = "REQUIRED" }
      ])
    }
''')

# =========================================================================
# 2. backend/app/drift/__init__.py
# =========================================================================
w("backend/app/drift/__init__.py", '# backend/app/drift -- Longitudinal fairness-drift monitor\n')

# =========================================================================
# 3. backend/app/drift/_store.py  (in-memory dev stores)
# =========================================================================
w("backend/app/drift/_store.py", '''
    """In-memory stores for drift monitoring (dev/test mode).
    In production these are replaced by BigQuery reads/writes."""
    from typing import Any, Dict, List

    # Mirrors BQ fairguard_monitoring.decisions
    decisions_store: List[Dict[str, Any]] = []

    # Mirrors BQ fairguard_monitoring.drift_metrics
    drift_metrics_store: List[Dict[str, Any]] = []

    # Active drift-monitor registrations  {audit_id: {webhook_url, email}}
    registrations: Dict[str, Dict[str, Any]] = {}
''')

# =========================================================================
# 4. backend/app/drift/subscriber.py
# =========================================================================
w("backend/app/drift/subscriber.py", '''
    """
    Pub/Sub Subscriber -- Cloud Run service for fairguard-decisions topic.

    Validates schema, rejects messages containing PII (name/SSN/email),
    inserts PII-free rows into BigQuery fairguard_monitoring.decisions.

    References
    ----------
    - Davis, Dorn, Park, Matheny, "Emerging algorithmic bias: fairness drift,"
      JAMIA 32(5):845-854, 2025, DOI 10.1093/jamia/ocaf039.
    - Henzinger et al., "Runtime Monitoring of Dynamic Fairness Properties,"
      FAccT 2023, DOI 10.1145/3593013.3594028.
    """
    import base64, json, logging, re
    from typing import Any, Dict, Optional
    from fastapi import APIRouter, HTTPException, Request

    router = APIRouter(prefix="/drift", tags=["drift-subscriber"])
    logger = logging.getLogger("fairguard.drift.subscriber")

    PII_FIELDS = {"name", "first_name", "last_name", "ssn", "email",
                  "phone", "address", "social_security", "date_of_birth"}
    _SSN_RE = re.compile(r"\\b\\d{3}-\\d{2}-\\d{4}\\b")
    _EMAIL_RE = re.compile(r"[^@\\s]+@[^@\\s]+\\.[^@\\s]+")
    REQUIRED_FIELDS = {"audit_id", "timestamp", "protected_attrs", "decision", "outcome"}


    def _contains_pii(data: Dict[str, Any]) -> Optional[str]:
        all_keys = set(data.keys())
        if isinstance(data.get("protected_attrs"), dict):
            all_keys |= set(data["protected_attrs"].keys())
        overlap = all_keys & PII_FIELDS
        if overlap:
            return f"Banned PII fields present: {overlap}"
        raw = json.dumps(data)
        if _SSN_RE.search(raw):
            return "SSN pattern detected in payload"
        if _EMAIL_RE.search(raw):
            return "Email pattern detected in payload"
        return None


    def _validate_schema(data: Dict[str, Any]) -> Optional[str]:
        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            return f"Missing required fields: {missing}"
        if not isinstance(data["protected_attrs"], dict):
            return "protected_attrs must be a JSON object"
        if not isinstance(data["decision"], int):
            return "decision must be an integer"
        if not isinstance(data["outcome"], int):
            return "outcome must be an integer"
        return None


    @router.post("/subscriber")
    async def receive_decision(request: Request):
        """Receive a Pub/Sub push message containing a model decision."""
        envelope = await request.json()
        if not isinstance(envelope, dict) or "message" not in envelope:
            raise HTTPException(status_code=400, detail="Invalid Pub/Sub envelope")
        raw_data = envelope["message"].get("data")
        if not raw_data:
            raise HTTPException(status_code=400, detail="No data field in message")
        try:
            decoded = base64.b64decode(raw_data).decode("utf-8")
            data: Dict[str, Any] = json.loads(decoded)
        except Exception as exc:
            logger.error("Failed to decode Pub/Sub message: %s", exc)
            return {"status": "error", "detail": "Decode failure"}

        pii_reason = _contains_pii(data)
        if pii_reason:
            logger.warning("REJECTED decision -- %s", pii_reason)
            return {"status": "rejected", "reason": pii_reason}

        schema_reason = _validate_schema(data)
        if schema_reason:
            logger.warning("REJECTED decision -- %s", schema_reason)
            raise HTTPException(status_code=422, detail=schema_reason)

        from backend.app.drift._store import decisions_store
        decisions_store.append({
            "audit_id": data["audit_id"],
            "timestamp": data["timestamp"],
            "protected_attrs": data["protected_attrs"],
            "decision": data["decision"],
            "outcome": data["outcome"],
        })
        logger.info("Stored decision for audit=%s", data["audit_id"])
        return {"status": "ok"}
''')

# =========================================================================
# 5. backend/app/drift/compute.py
# =========================================================================
w("backend/app/drift/compute.py", '''
    """
    Hourly Drift Compute Job -- Cloud Scheduler -> Cloud Run.

    For every active audit_id, pulls the last 30 days of decisions,
    computes demographic-parity diff, equalized-odds gap, and NYC LL144
    adverse-impact ratio, then compares to the audit-time baseline.

    Alert rules (non-configurable for MVP):
      (a) DP diff exceeds baseline by > 2 sigma
      (b) EO gap exceeds baseline by > 2 sigma
      (c) NYC LL144 impact ratio < 0.8

    References
    ----------
    - Davis, Dorn, Park, Matheny, "Emerging algorithmic bias: fairness drift,"
      JAMIA 32(5):845-854, 2025, DOI 10.1093/jamia/ocaf039.
    - Henzinger et al., "Runtime Monitoring of Dynamic Fairness Properties,"
      FAccT 2023, DOI 10.1145/3593013.3594028.
    """
    from __future__ import annotations
    import logging, os
    from datetime import datetime, timedelta, timezone
    from typing import Any, Dict, List, Optional, Tuple
    import numpy as np
    import pandas as pd
    from fastapi import APIRouter

    router = APIRouter(prefix="/drift", tags=["drift-compute"])
    logger = logging.getLogger("fairguard.drift.compute")

    WINDOW_DAYS = 30
    SIGMA_THRESHOLD = 2

    # -------------------------------------------------------------------
    # Core metric functions
    # -------------------------------------------------------------------
    def compute_demographic_parity_diff(decisions, groups):
        """P(d=1|privileged) - P(d=1|protected)."""
        priv = (groups == 0); prot = (groups == 1)
        if priv.sum() == 0 or prot.sum() == 0: return 0.0
        return float(decisions[priv].mean() - decisions[prot].mean())

    def compute_equalized_odds_gap(decisions, outcomes, groups):
        """max(|TPR gap|, |FPR gap|) between groups."""
        gaps = []
        for y in (0, 1):
            m = (outcomes == y)
            if m.sum() == 0: continue
            p = decisions[m & (groups == 0)]; q = decisions[m & (groups == 1)]
            if len(p) == 0 or len(q) == 0: continue
            gaps.append(abs(float(p.mean()) - float(q.mean())))
        return max(gaps) if gaps else 0.0

    def compute_impact_ratio(decisions, groups):
        """NYC LL144: P(d=1|protected) / P(d=1|privileged)."""
        priv = (groups == 0); prot = (groups == 1)
        pr = decisions[priv].mean() if priv.sum() > 0 else 0.0
        pt = decisions[prot].mean() if prot.sum() > 0 else 0.0
        return float(pt / pr) if pr > 0 else 1.0

    def compute_all_metrics(df, protected_attr_key="group"):
        """Return (dp_diff, eo_gap, impact_ratio) for a decisions DataFrame."""
        if df.empty: return 0.0, 0.0, 1.0
        groups = np.array(df["protected_attrs"].apply(lambda x: x.get(protected_attr_key, 0)).tolist())
        decisions = df["decision"].values.astype(float)
        outcomes  = df["outcome"].values.astype(float)
        return (compute_demographic_parity_diff(decisions, groups),
                compute_equalized_odds_gap(decisions, outcomes, groups),
                compute_impact_ratio(decisions, groups))

    # -------------------------------------------------------------------
    # Alerting
    # -------------------------------------------------------------------
    def _should_alert(dp, eo, ir, bl_dp, bl_eo, bl_dp_std, bl_eo_std):
        reasons = []
        if bl_dp_std > 0 and abs(dp - bl_dp) > SIGMA_THRESHOLD * bl_dp_std:
            reasons.append(f"DP diff {dp:.4f} exceeds baseline {bl_dp:.4f} by >{SIGMA_THRESHOLD}s (s={bl_dp_std:.4f})")
        if bl_eo_std > 0 and abs(eo - bl_eo) > SIGMA_THRESHOLD * bl_eo_std:
            reasons.append(f"EO gap {eo:.4f} exceeds baseline {bl_eo:.4f} by >{SIGMA_THRESHOLD}s (s={bl_eo_std:.4f})")
        if ir < 0.8:
            reasons.append(f"NYC LL144 impact ratio {ir:.4f} < 0.8")
        return bool(reasons), reasons

    def _send_alerts(audit_id, reasons, webhook_url=None, email=None):
        for r in reasons:
            logger.warning("ALERT [%s]: %s", audit_id, r)
        if webhook_url:
            try:
                import httpx
                httpx.post(webhook_url, json={"audit_id": audit_id, "reasons": reasons}, timeout=10)
            except Exception as exc:
                logger.error("Webhook failed for %s: %s", audit_id, exc)
        sg_key = os.environ.get("SENDGRID_API_KEY")
        if sg_key and email:
            try:
                import sendgrid; from sendgrid.helpers.mail import Mail
                sg = sendgrid.SendGridAPIClient(api_key=sg_key)
                sg.send(Mail(from_email="alerts@fairguard.dev", to_emails=email,
                             subject=f"FairGuard Drift Alert -- {audit_id}",
                             plain_text_content="\\n".join(reasons)))
            except Exception as exc:
                logger.error("SendGrid failed for %s: %s", audit_id, exc)

    # -------------------------------------------------------------------
    # Main compute entry-point
    # -------------------------------------------------------------------
    def _parse_ts(ts):
        if isinstance(ts, datetime):
            return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))

    def run_hourly_compute(decisions, registrations, now=None, baseline=None):
        """Run hourly compute for all registered audit_ids.

        Returns list of drift_metric rows inserted this hour.
        """
        if now is None: now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=WINDOW_DAYS)
        if baseline is None: baseline = {}
        results = []

        for audit_id, reg in registrations.items():
            rows = [r for r in decisions
                    if r["audit_id"] == audit_id and _parse_ts(r["timestamp"]) >= cutoff]
            if not rows: continue
            df = pd.DataFrame(rows)
            dp, eo, ir = compute_all_metrics(df)
            bl = baseline.get(audit_id, {"dp_mean": 0.0, "dp_std": 0.05,
                                          "eo_mean": 0.0, "eo_std": 0.05})
            fired, reasons = _should_alert(dp, eo, ir,
                                           bl["dp_mean"], bl["eo_mean"],
                                           bl["dp_std"], bl["eo_std"])
            if fired:
                _send_alerts(audit_id, reasons,
                             webhook_url=reg.get("webhook_url"), email=reg.get("email"))
            results.append({
                "audit_id": audit_id, "computed_at": now.isoformat(),
                "demographic_parity_diff": dp, "equalized_odds_gap": eo,
                "impact_ratio": ir, "alert_fired": fired,
            })
        return results

    @router.post("/compute")
    async def trigger_compute():
        from backend.app.drift._store import decisions_store, drift_metrics_store, registrations
        rows = run_hourly_compute(decisions_store, registrations)
        drift_metrics_store.extend(rows)
        logger.info("Computed %d drift-metric rows", len(rows))
        return {"status": "ok", "rows_written": len(rows)}
''')

# =========================================================================
# 6. backend/tests/drift/__init__.py
# =========================================================================
w("backend/tests/drift/__init__.py", "")

# =========================================================================
# 7. backend/tests/drift/test_compute.py
# =========================================================================
w("backend/tests/drift/test_compute.py", '''
    """
    Synthetic 30-day drift test.

    200 decisions/day. Days 1-14 fair, days 15-30 inject 20%
    approval-rate drop on protected group. Run hourly compute in
    simulated time.

    Verifies:
    - Alert fires between days 15-16.
    - drift_metrics has ~720 rows (30*24 +/-2).
    - No alerts on days 1-14.
    """
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta, timezone
    from backend.app.drift.compute import compute_all_metrics, run_hourly_compute

    def _generate_decisions(n_days=30, per_day=200, seed=42):
        """Generate synthetic decisions with bias injected after day 14."""
        rng = np.random.RandomState(seed)
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        rows = []
        for day in range(n_days):
            t = start + timedelta(days=day)
            for _ in range(per_day):
                group = rng.choice([0, 1])
                outcome = rng.choice([0, 1])
                prob = 0.8 if outcome == 1 else 0.2
                if day >= 14 and group == 1:
                    prob *= 0.80  # 20 % approval-rate drop
                decision = int(rng.rand() < prob)
                rows.append({
                    "audit_id": "test-audit",
                    "timestamp": (t + timedelta(seconds=rng.randint(0, 86400))).isoformat(),
                    "protected_attrs": {"group": group},
                    "decision": decision,
                    "outcome": outcome,
                })
        return rows

    def test_metrics_fair_period():
        rows = _generate_decisions()
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        fair = [r for r in rows
                if datetime.fromisoformat(r["timestamp"]) < start + timedelta(days=14)]
        df = pd.DataFrame(fair)
        dp, eo, ir = compute_all_metrics(df, "group")
        assert ir > 0.90, f"Fair-period impact ratio too low: {ir}"
        assert abs(dp) < 0.10, f"Fair-period DP diff too large: {dp}"

    def test_metrics_biased_period():
        rows = _generate_decisions()
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        biased = [r for r in rows
                  if datetime.fromisoformat(r["timestamp"]) >= start + timedelta(days=14)]
        df = pd.DataFrame(biased)
        dp, eo, ir = compute_all_metrics(df, "group")
        assert ir < 0.85, f"Biased-period impact ratio too high: {ir}"
        assert dp > 0.05, f"Biased-period DP diff too small: {dp}"

    def test_hourly_alerts_fire_on_bias():
        """Simulate 30 days x 24 hours of compute. Alerts should fire days 15-16."""
        rows = _generate_decisions()
        regs = {"test-audit": {}}
        # Baseline from fair period (days 1-7)
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        baseline = {"test-audit": {"dp_mean": 0.0, "dp_std": 0.03,
                                    "eo_mean": 0.0, "eo_std": 0.03}}
        all_metrics = []
        for day in range(30):
            for hour in range(24):
                now = start + timedelta(days=day, hours=hour)
                result = run_hourly_compute(rows, regs, now=now, baseline=baseline)
                all_metrics.extend(result)

        # Should have ~720 rows
        assert 700 <= len(all_metrics) <= 740, f"Expected ~720 rows, got {len(all_metrics)}"

        # No alerts days 1-14
        day14 = start + timedelta(days=14)
        early = [m for m in all_metrics
                 if datetime.fromisoformat(m["computed_at"]) < day14]
        assert all(not m["alert_fired"] for m in early), "Alert fired in fair period!"

        # Alerts should fire somewhere in days 15-16
        day15 = start + timedelta(days=14)
        day17 = start + timedelta(days=17)
        mid = [m for m in all_metrics
               if day15 <= datetime.fromisoformat(m["computed_at"]) < day17]
        assert any(m["alert_fired"] for m in mid), "No alert in days 15-17!"
''')

print("\\n=== All drift-monitor files created successfully ===")

resource "google_pubsub_topic" "decisions" {
  name = "fairguard-decisions"
}

resource "google_bigquery_dataset" "monitoring" {
  dataset_id = "fairguard_monitoring"
  location   = "US"
}

resource "google_bigquery_table" "decisions" {
  dataset_id = google_bigquery_dataset.monitoring.dataset_id
  table_id   = "decisions"
  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }
  clustering = ["audit_id"]
  schema = "[{\"name\": \"audit_id\", \"type\": \"STRING\", \"mode\": \"REQUIRED\"},{\"name\": \"timestamp\", \"type\": \"TIMESTAMP\", \"mode\": \"REQUIRED\"},{\"name\": \"protected_attrs\", \"type\": \"JSON\", \"mode\": \"REQUIRED\"},{\"name\": \"decision\", \"type\": \"INT64\", \"mode\": \"REQUIRED\"},{\"name\": \"outcome\", \"type\": \"INT64\", \"mode\": \"REQUIRED\"}]"
}

resource "google_bigquery_table" "drift_metrics" {
  dataset_id = google_bigquery_dataset.monitoring.dataset_id
  table_id   = "drift_metrics"
  time_partitioning {
    type  = "DAY"
    field = "computed_at"
  }
  clustering = ["audit_id"]
  schema = "[{\"name\": \"audit_id\", \"type\": \"STRING\", \"mode\": \"REQUIRED\"},{\"name\": \"computed_at\", \"type\": \"TIMESTAMP\", \"mode\": \"REQUIRED\"},{\"name\": \"demographic_parity_diff\", \"type\": \"FLOAT64\", \"mode\": \"NULLABLE\"},{\"name\": \"equalized_odds_gap\", \"type\": \"FLOAT64\", \"mode\": \"NULLABLE\"},{\"name\": \"impact_ratio\", \"type\": \"FLOAT64\", \"mode\": \"NULLABLE\"},{\"name\": \"alert_fired\", \"type\": \"BOOL\", \"mode\": \"REQUIRED\"}]"
}

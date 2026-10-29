
import pyodbc
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "CloudMonitoring"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

CONTAMINATION = 0.10
MIN_RECORDS = 20


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)


def detect_anomalies(
    df,
    features,
    source_name,
    output_table,
    insert_columns,
    id_column="id"
):
    if df.empty:
        print(f"{source_name}: no observations found.")
        return

    # Convert selected features to numeric and clean invalid values.
    for feature in features:
        df[feature] = pd.to_numeric(df[feature], errors="coerce")

    df = df.dropna(subset=features).copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=features).copy()

    if len(df) < MIN_RECORDS:
        print(
            f"{source_name}: only {len(df)} valid records; "
            f"need at least {MIN_RECORDS}. Skipping."
        )
        return

    # Constant features do not help identify multivariate anomalies.
    usable_features = [
        feature for feature in features
        if df[feature].nunique() > 1
    ]

    if not usable_features:
        print(
            f"{source_name}: all selected metrics are constant. "
            "Skipping detection until data varies."
        )
        return

    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        random_state=42
    )

    df["anomaly_prediction"] = model.fit_predict(
        df[usable_features]
    )
    df["anomaly_score"] = model.decision_function(
        df[usable_features]
    )
    df["anomaly_status"] = np.where(
        df["anomaly_prediction"] == -1,
        "Anomaly",
        "Normal"
    )

    # Replace the previous results for this source.
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"DELETE FROM {output_table}")

        placeholders = ", ".join(["?"] * len(insert_columns))
        columns_sql = ", ".join(insert_columns)

        sql = (
            f"INSERT INTO {output_table} ({columns_sql}) "
            f"VALUES ({placeholders})"
        )

        for _, row in df.iterrows():
            values = []

            for column in insert_columns:
                if column == "metric_id":
                    values.append(int(row[id_column]))
                elif column == "anomaly_score":
                    values.append(float(row["anomaly_score"]))
                elif column == "anomaly_status":
                    values.append(row["anomaly_status"])
                else:
                    value = row[column]
                    values.append(
                        None if pd.isna(value) else value
                    )

            cursor.execute(sql, tuple(values))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()

    anomaly_count = int((df["anomaly_status"] == "Anomaly").sum())

    print(f"\n{source_name}")
    print(f"Records analyzed: {len(df)}")
    print(f"Features used: {usable_features}")
    print(f"Anomalies: {anomaly_count}")
    print(f"Normal: {len(df) - anomaly_count}")
    print(f"Anomaly rate: {anomaly_count / len(df) * 100:.2f}%")


def main():
    print("=" * 60)
    print("UNIFIED INFRASTRUCTURE ANOMALY DETECTION")
    print("=" * 60)

    conn = get_connection()

    try:
        system = pd.read_sql_query(
            """
            SELECT id, timestamp, cpu_usage, memory_usage, disk_usage
            FROM system_metrics
            ORDER BY timestamp
            """,
            conn
        )

        docker = pd.read_sql_query(
            """
            SELECT id, timestamp, container_id, container_name,
                   status, cpu_percent, memory_usage_mb,
                   memory_percent, network_received_mb,
                   network_sent_mb
            FROM docker_metrics
            ORDER BY timestamp
            """,
            conn
        )

        kubernetes = pd.read_sql_query(
            """
            SELECT id, timestamp, node_name, pod_name, namespace,
                   status, cpu_usage_millicores, memory_usage_mb
            FROM kubernetes_metrics
            ORDER BY timestamp
            """,
            conn
        )

    finally:
        conn.close()

    detect_anomalies(
        system,
        ["cpu_usage", "memory_usage", "disk_usage"],
        "HOST / SYSTEM",
        "system_anomalies",
        [
            "metric_id", "timestamp", "cpu_usage", "memory_usage",
            "disk_usage", "anomaly_score", "anomaly_status"
        ]
    )

    detect_anomalies(
        docker,
        [
            "cpu_percent", "memory_usage_mb", "memory_percent",
            "network_received_mb", "network_sent_mb"
        ],
        "DOCKER CONTAINERS",
        "docker_anomalies",
        [
            "metric_id", "timestamp", "container_id",
            "container_name", "cpu_percent", "memory_usage_mb",
            "memory_percent", "network_received_mb",
            "network_sent_mb", "anomaly_score", "anomaly_status"
        ]
    )

    detect_anomalies(
        kubernetes,
        ["cpu_usage_millicores", "memory_usage_mb"],
        "KUBERNETES PODS",
        "kubernetes_anomalies",
        [
            "metric_id", "timestamp", "node_name", "pod_name",
            "namespace", "status", "cpu_usage_millicores",
            "memory_usage_mb", "anomaly_score", "anomaly_status"
        ]
    )

    print("\nUnified anomaly detection finished.")


if __name__ == "__main__":
    main()

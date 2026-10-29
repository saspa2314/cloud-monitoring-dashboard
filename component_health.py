
import pyodbc

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "CloudMonitoring"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

TABLES = {
    "System": "system_anomalies",
    "Docker": "docker_anomalies",
    "Kubernetes": "kubernetes_anomalies",
}


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)


def assess_health(records, anomalies):
    if records == 0:
        return None, "Unknown", "No observations available"

    rate = anomalies / records

    # A transparent heuristic, not a trained ML prediction.
    score = max(0.0, min(100.0, 100.0 - rate * 200.0))

    if rate >= 0.20:
        status = "Critical"
    elif rate >= 0.10:
        status = "Warning"
    else:
        status = "Healthy"

    message = (
        f"{anomalies} anomalous observations out of {records}; "
        f"anomaly rate {rate * 100:.2f}%"
    )

    return round(score, 2), status, message


def main():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        results = []

        for component, table in TABLES.items():
            cursor.execute(
                f"""
                SELECT
                    COUNT(*) AS records,
                    COALESCE(
                        SUM(CASE
                            WHEN anomaly_status = 'Anomaly'
                            THEN 1 ELSE 0
                        END),
                        0
                    ) AS anomalies
                FROM {table}
                """
            )

            records, anomalies = cursor.fetchone()
            records = int(records)
            anomalies = int(anomalies)

            score, status, message = assess_health(
                records, anomalies
            )

            rate = (
                anomalies / records
                if records > 0 else None
            )

            results.append({
                "component": component,
                "records": records,
                "anomalies": anomalies,
                "rate": rate,
                "score": score,
                "status": status,
                "message": message,
            })

        # Do not treat an unavailable component as healthy.
        available = [
            r for r in results
            if r["score"] is not None
        ]

        overall_score = (
            round(
                sum(r["score"] for r in available)
                / len(available),
                2
            )
            if available else None
        )

        cursor.execute("DELETE FROM component_health")

        for r in results:
            cursor.execute(
                """
                INSERT INTO component_health (
                    component_name,
                    records_analyzed,
                    anomaly_count,
                    anomaly_rate,
                    health_score,
                    health_status,
                    status_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                r["component"],
                r["records"],
                r["anomalies"],
                r["rate"],
                r["score"],
                r["status"],
                r["message"],
            )

        conn.commit()

        print("\nCOMPONENT HEALTH ASSESSMENT")
        print("-" * 60)

        for r in results:
            print(
                f'{r["component"]:12} | '
                f'Records: {r["records"]:4} | '
                f'Anomalies: {r["anomalies"]:3} | '
                f'Score: {r["score"]} | '
                f'Status: {r["status"]}'
            )

        print("-" * 60)
        print(f"Overall component health score: {overall_score}")

        if len(available) != len(results):
            print(
                "Warning: at least one component has no data; "
                "the overall score excludes unavailable components."
            )

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()

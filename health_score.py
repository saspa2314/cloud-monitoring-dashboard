import pyodbc
import pandas as pd


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "CloudMonitoring"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)


# ============================================================
# LOAD ANOMALY RESULTS
# ============================================================

def load_anomaly_results():

    conn = pyodbc.connect(CONNECTION_STRING)

    query = """
        SELECT
            metric_id,
            timestamp,
            cpu_usage,
            memory_usage,
            disk_usage,
            anomaly_score,
            anomaly_status
        FROM system_anomalies
        ORDER BY timestamp
    """

    df = pd.read_sql(query, conn)

    conn.close()

    return df


# ============================================================
# CALCULATE HEALTH SCORE
# ============================================================

def calculate_health_score(row):

    # Start with maximum health
    score = 100.0

    # --------------------------------------------------------
    # CPU penalty
    # --------------------------------------------------------

    if row["cpu_usage"] >= 90:
        score -= 30

    elif row["cpu_usage"] >= 80:
        score -= 20

    elif row["cpu_usage"] >= 70:
        score -= 10

    # --------------------------------------------------------
    # Memory penalty
    # --------------------------------------------------------

    if row["memory_usage"] >= 95:
        score -= 30

    elif row["memory_usage"] >= 90:
        score -= 20

    elif row["memory_usage"] >= 80:
        score -= 10

    # --------------------------------------------------------
    # Disk penalty
    # --------------------------------------------------------

    if row["disk_usage"] >= 90:
        score -= 20

    elif row["disk_usage"] >= 80:
        score -= 10

    # --------------------------------------------------------
    # ML anomaly penalty
    # --------------------------------------------------------

    if row["anomaly_status"] == "Anomaly":
        score -= 20

    # Keep score between 0 and 100
    score = max(0, min(100, score))

    return score


# ============================================================
# HEALTH STATUS
# ============================================================

def get_health_status(score):

    if score >= 80:
        return "Healthy"

    elif score >= 60:
        return "Warning"

    else:
        return "Critical"


# ============================================================
# CREATE HEALTH RESULTS
# ============================================================

def create_health_results(df):

    df["health_score"] = df.apply(
        calculate_health_score,
        axis=1
    )

    df["health_status"] = df["health_score"].apply(
        get_health_status
    )

    return df


# ============================================================
# SAVE HEALTH RESULTS
# ============================================================

def save_health_results(df):

    conn = pyodbc.connect(CONNECTION_STRING)
    cursor = conn.cursor()

    # Remove previous health results
    cursor.execute(
        "DELETE FROM infrastructure_health"
    )

    for _, row in df.iterrows():

        cursor.execute(
            """
            INSERT INTO infrastructure_health
            (
                timestamp,
                cpu_usage,
                memory_usage,
                disk_usage,
                anomaly_score,
                anomaly_status,
                health_score,
                health_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            row["timestamp"],
            float(row["cpu_usage"]),
            float(row["memory_usage"]),
            float(row["disk_usage"]),
            float(row["anomaly_score"]),
            str(row["anomaly_status"]),
            float(row["health_score"]),
            str(row["health_status"])
        )

    conn.commit()

    cursor.close()
    conn.close()

    print("\nHealth results saved to SQL Server.")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("INFRASTRUCTURE HEALTH SCORE")
    print("=" * 60)

    print("\nLoading anomaly results...")

    df = load_anomaly_results()

    print(
        f"Records loaded: {len(df)}"
    )

    if len(df) == 0:

        print(
            "No anomaly results found."
        )

        print(
            "Run anomaly_detection.py first."
        )

        exit()

    # Calculate health
    result = create_health_results(df)

    # Save to database
    save_health_results(result)

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\nHealth Status Summary")
    print("=" * 60)

    print(
        result["health_status"].value_counts()
    )

    print("\nAverage Health Score:")

    print(
        f"{result['health_score'].mean():.2f} / 100"
    )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print("\nHealth Score Results")
    print("=" * 60)

    print(
        result[
            [
                "timestamp",
                "cpu_usage",
                "memory_usage",
                "disk_usage",
                "anomaly_status",
                "anomaly_score",
                "health_score",
                "health_status"
            ]
        ].to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("HEALTH SCORE CALCULATION COMPLETED")
    print("=" * 60)
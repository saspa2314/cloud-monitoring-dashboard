import pyodbc
from datetime import datetime

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "CloudMonitoring"

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)

conn = pyodbc.connect(CONNECTION_STRING)
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO system_anomalies
    (
        metric_id,
        timestamp,
        cpu_usage,
        memory_usage,
        disk_usage,
        anomaly_score,
        anomaly_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
    999,
    datetime.now(),
    100.0,
    96.0,
    9.8,
    -0.01,
    "Anomaly"
)

conn.commit()

cursor.close()
conn.close()

print("TEST INSERT SUCCESSFUL")
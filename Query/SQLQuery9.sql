CREATE TABLE system_anomalies (
    id INT IDENTITY(1,1) PRIMARY KEY,
    metric_id INT,
    timestamp DATETIME,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    anomaly_score FLOAT,
    anomaly_status VARCHAR(20)
);
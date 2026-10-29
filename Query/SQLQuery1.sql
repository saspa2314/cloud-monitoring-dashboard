CREATE DATABASE CloudMonitoring;
GO
USE CloudMonitoring;
GO
CREATE TABLE system_metrics (
    id INT IDENTITY(1,1) PRIMARY KEY,
    timestamp DATETIME2 NOT NULL,
    cpu_usage FLOAT NOT NULL,
    memory_usage FLOAT NOT NULL,
    disk_usage FLOAT NOT NULL,
    bytes_sent BIGINT NOT NULL,
    bytes_received BIGINT NOT NULL
);
GO
SELECT * FROM system_metrics;
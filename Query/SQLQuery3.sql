CREATE TABLE docker_metrics (
    id INT IDENTITY(1,1) PRIMARY KEY,
    timestamp DATETIME DEFAULT GETDATE(),
    container_id VARCHAR(100),
    container_name VARCHAR(200),
    status VARCHAR(50),
    cpu_percent FLOAT,
    memory_usage_mb FLOAT,
    memory_percent FLOAT,
    network_received_mb FLOAT,
    network_sent_mb FLOAT
);
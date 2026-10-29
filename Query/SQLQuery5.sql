USE cloudmonitoring;
GO

CREATE TABLE kubernetes_metrics (
    id INT IDENTITY(1,1) PRIMARY KEY,
    timestamp DATETIME DEFAULT GETDATE(),
    node_name VARCHAR(200),
    pod_name VARCHAR(200),
    namespace VARCHAR(100),
    status VARCHAR(50),
    cpu_request VARCHAR(50),
    memory_request VARCHAR(50),
    cpu_limit VARCHAR(50),
    memory_limit VARCHAR(50)
);
GO
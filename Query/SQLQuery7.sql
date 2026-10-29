ALTER TABLE kubernetes_metrics
ADD
    cpu_usage_millicores FLOAT NULL,
    memory_usage_mb FLOAT NULL;
GO
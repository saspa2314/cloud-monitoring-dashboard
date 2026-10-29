SELECT TOP 20
    timestamp,
    pod_name,
    status,
    cpu_usage_millicores,
    memory_usage_mb
FROM kubernetes_metrics
ORDER BY id DESC;
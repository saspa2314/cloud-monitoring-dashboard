from kubernetes import client, config
from datetime import datetime
import time

from database import get_connection


# --------------------------------------------------
# LOAD KUBERNETES CONFIGURATION
# --------------------------------------------------

config.load_kube_config()

v1 = client.CoreV1Api()
custom_api = client.CustomObjectsApi()

NAMESPACE = "cloud-monitoring"


# --------------------------------------------------
# CONVERT CPU TO MILLICORES
# --------------------------------------------------

def parse_cpu(cpu):
    """
    Convert Kubernetes CPU quantity into millicores.

    Examples:
        1      -> 1000
        500m   -> 500
        100m   -> 100
        1n     -> 0.000001
    """

    if cpu is None:
        return 0.0

    cpu = str(cpu)

    try:
        if cpu.endswith("n"):
            return float(cpu[:-1]) / 1_000_000

        elif cpu.endswith("u"):
            return float(cpu[:-1]) / 1_000

        elif cpu.endswith("m"):
            return float(cpu[:-1])

        else:
            return float(cpu) * 1000

    except ValueError:
        return 0.0


# --------------------------------------------------
# CONVERT MEMORY TO MB
# --------------------------------------------------

def parse_memory(memory):
    """
    Convert Kubernetes memory quantity into MB.

    Examples:
        10Mi -> approximately 10.48 MB
        1Gi  -> approximately 1073.74 MB
        100Ki -> approximately 0.10 MB
    """

    if memory is None:
        return 0.0

    memory = str(memory)

    try:

        if memory.endswith("Ki"):
            return float(memory[:-2]) / 1024

        elif memory.endswith("Mi"):
            return float(memory[:-2]) * 1024 / 1000

        elif memory.endswith("Gi"):
            return float(memory[:-2]) * 1024 * 1024 / 1000

        elif memory.endswith("Ti"):
            return float(memory[:-2]) * 1024 * 1024 * 1024 / 1000

        elif memory.endswith("K"):
            return float(memory[:-1]) / 1000

        elif memory.endswith("M"):
            return float(memory[:-1])

        elif memory.endswith("G"):
            return float(memory[:-1]) * 1000

        else:
            # Assume bytes
            return float(memory) / (1024 * 1024)

    except ValueError:
        return 0.0


# --------------------------------------------------
# GET RESOURCE REQUESTS AND LIMITS
# --------------------------------------------------

def get_container_resources(pod):

    cpu_request = None
    memory_request = None
    cpu_limit = None
    memory_limit = None

    if pod.spec.containers:

        container = pod.spec.containers[0]

        resources = container.resources

        if resources:

            requests = resources.requests or {}
            limits = resources.limits or {}

            cpu_request = requests.get("cpu")
            memory_request = requests.get("memory")

            cpu_limit = limits.get("cpu")
            memory_limit = limits.get("memory")

    return (
        cpu_request,
        memory_request,
        cpu_limit,
        memory_limit
    )


# --------------------------------------------------
# COLLECT KUBERNETES METRICS
# --------------------------------------------------

def collect_kubernetes_metrics():

    try:

        # ------------------------------------------
        # GET POD INFORMATION
        # ------------------------------------------

        pods = v1.list_namespaced_pod(
            namespace=NAMESPACE
        )

        # ------------------------------------------
        # GET ACTUAL POD METRICS
        # ------------------------------------------
        metrics = custom_api.list_namespaced_custom_object(
        group="metrics.k8s.io",
        version="v1beta1",
        namespace=NAMESPACE,
        plural="pods"
)

        metric_items = metrics.get("items", [])

        # ------------------------------------------
        # CREATE LOOKUP TABLE
        # ------------------------------------------

        pod_metrics = {}

        for item in metric_items:

            pod_name = item["metadata"]["name"]

            total_cpu = 0.0
            total_memory = 0.0

            for container in item.get("containers", []):

                usage = container.get("usage", {})

                cpu = usage.get("cpu", "0")
                memory = usage.get("memory", "0")

                total_cpu += parse_cpu(cpu)
                total_memory += parse_memory(memory)

            pod_metrics[pod_name] = {
                "cpu": total_cpu,
                "memory": total_memory
            }

        # ------------------------------------------
        # CONNECT TO SQL SERVER
        # ------------------------------------------

        connection = get_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO kubernetes_metrics
            (
                timestamp,
                node_name,
                pod_name,
                namespace,
                status,
                cpu_request,
                memory_request,
                cpu_limit,
                memory_limit,
                cpu_usage_millicores,
                memory_usage_mb
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0

        # ------------------------------------------
        # PROCESS EACH POD
        # ------------------------------------------

        for pod in pods.items:

            pod_name = pod.metadata.name

            namespace = pod.metadata.namespace

            node_name = pod.spec.node_name

            status = pod.status.phase

            (
                cpu_request,
                memory_request,
                cpu_limit,
                memory_limit
            ) = get_container_resources(pod)

            # --------------------------------------
            # GET ACTUAL USAGE
            # --------------------------------------

            actual_cpu = 0.0
            actual_memory = 0.0

            if pod_name in pod_metrics:

                actual_cpu = pod_metrics[pod_name]["cpu"]

                actual_memory = pod_metrics[pod_name]["memory"]

            # --------------------------------------
            # INSERT INTO SQL SERVER
            # --------------------------------------

            cursor.execute(
                query,
                datetime.now(),
                node_name,
                pod_name,
                namespace,
                status,
                cpu_request,
                memory_request,
                cpu_limit,
                memory_limit,
                actual_cpu,
                actual_memory
            )

            inserted += 1

        connection.commit()

        cursor.close()
        connection.close()

        print(
            f"[{datetime.now()}] "
            f"Kubernetes metrics collected: "
            f"{inserted} pods"
        )

    except Exception as e:

        print(
            f"[{datetime.now()}] "
            f"Error collecting Kubernetes metrics: {e}"
        )


# --------------------------------------------------
# CONTINUOUS MONITORING
# --------------------------------------------------

print("========================================")
print(" Kubernetes Monitoring Started")
print(" Namespace:", NAMESPACE)
print(" Interval: 5 seconds")
print("========================================")


while True:

    collect_kubernetes_metrics()

    time.sleep(5)
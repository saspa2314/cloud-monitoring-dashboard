import docker
import time
from datetime import datetime
from database import get_connection

client = docker.from_env()


def calculate_cpu_percent(stats):

    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )

    system_delta = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )

    if system_delta > 0 and cpu_delta > 0:

        cpu_count = stats["cpu_stats"].get(
            "online_cpus", 1
        )

        return (cpu_delta / system_delta) * cpu_count * 100

    return 0.0


def collect_docker_metrics():

    containers = client.containers.list()

    connection = get_connection()
    cursor = connection.cursor()

    for container in containers:

        stats = container.stats(stream=False)

        cpu_percent = calculate_cpu_percent(stats)

        memory_usage = (
            stats["memory_stats"].get("usage", 0)
            / (1024 * 1024)
        )

        memory_limit = stats["memory_stats"].get("limit", 0)

        if memory_limit > 0:
            memory_percent = (
                stats["memory_stats"]["usage"]
                / memory_limit
            ) * 100
        else:
            memory_percent = 0

        networks = stats.get("networks", {})

        network_received = 0
        network_sent = 0

        for network in networks.values():

            network_received += network.get("rx_bytes", 0)
            network_sent += network.get("tx_bytes", 0)

        network_received_mb = (
            network_received / (1024 * 1024)
        )

        network_sent_mb = (
            network_sent / (1024 * 1024)
        )

        cursor.execute(
            """
            INSERT INTO docker_metrics
            (
                timestamp,
                container_id,
                container_name,
                status,
                cpu_percent,
                memory_usage_mb,
                memory_percent,
                network_received_mb,
                network_sent_mb
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(),
                container.id,
                container.name,
                container.status,
                cpu_percent,
                memory_usage,
                memory_percent,
                network_received_mb,
                network_sent_mb
            )
        )

        print(
            f"{container.name} | "
            f"CPU: {cpu_percent:.2f}% | "
            f"Memory: {memory_usage:.2f} MB | "
            f"Status: {container.status}"
        )

    connection.commit()

    cursor.close()
    connection.close()


if __name__ == "__main__":

    print("Docker monitoring started...")

    while True:

        try:
            collect_docker_metrics()

        except Exception as e:
            print("Error:", e)

        time.sleep(5)
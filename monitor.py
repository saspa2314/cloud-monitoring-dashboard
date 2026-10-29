import psutil
import time
from datetime import datetime
from database import get_connection


def collect_metrics():

    cpu_usage = psutil.cpu_percent(interval=1)

    memory_usage = psutil.virtual_memory().percent

    disk_usage = psutil.disk_usage("/").percent

    network = psutil.net_io_counters()

    bytes_sent = network.bytes_sent
    bytes_received = network.bytes_recv

    timestamp = datetime.now()

    return (
        timestamp,
        cpu_usage,
        memory_usage,
        disk_usage,
        bytes_sent,
        bytes_received
    )


def save_metrics(metrics):

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO system_metrics
    (
        timestamp,
        cpu_usage,
        memory_usage,
        disk_usage,
        bytes_sent,
        bytes_received
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """

    cursor.execute(query, metrics)

    connection.commit()

    cursor.close()
    connection.close()


# Continuous monitoring
while True:

    try:

        metrics = collect_metrics()

        save_metrics(metrics)

        print("--------------------------------")
        print(f"Time           : {metrics[0]}")
        print(f"CPU Usage      : {metrics[1]:.2f}%")
        print(f"Memory Usage   : {metrics[2]:.2f}%")
        print(f"Disk Usage     : {metrics[3]:.2f}%")
        print(f"Bytes Sent     : {metrics[4]}")
        print(f"Bytes Received : {metrics[5]}")
        print("Data saved to SQL Server")

        # Wait 5 seconds
        time.sleep(5)

    except Exception as e:

        print("Error:", e)

        # Wait before trying again
        time.sleep(5)
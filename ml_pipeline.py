
import subprocess
import sys
import time
import pyodbc

SERVER = r"localhost\SQLEXPRESS"
DATABASE = "CloudMonitoring"

CHECK_INTERVAL = 30
RETRAIN_AFTER = 10

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
)


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)


def get_metric_count():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM system_metrics")
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        conn.close()


def run_script(script):
    print(f"\n{'=' * 60}\nRunning {script}\n{'=' * 60}")

    result = subprocess.run(
        [sys.executable, script],
        check=False
    )

    if result.returncode != 0:
        print(f"ERROR: {script} failed with code {result.returncode}")
        return False

    return True


def run_pipeline():
    # Unified detection processes system, Docker and Kubernetes.
    if not run_script("anomaly_detection.py"):
        return False

    # Update the host-level health score.
    if not run_script("health_score.py"):
        return False

    # Update System, Docker and Kubernetes component health.
    if not run_script("component_health.py"):
        return False

    return True


def main():
    print("=" * 60)
    print("CONTINUOUS CLOUD INFRASTRUCTURE ML PIPELINE")
    print("=" * 60)

    last_count = get_metric_count()

    if not run_pipeline():
        print("Initial pipeline failed. Fix the error before continuing.")
        sys.exit(1)

    last_count = get_metric_count()
    print("\nContinuous monitoring is active.")
    print(f"Checking for new system observations every {CHECK_INTERVAL}s.")

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            current_count = get_metric_count()
            new_records = current_count - last_count

            print(
                f"\n{time.strftime('%H:%M:%S')} | "
                f"System observations: {current_count} | "
                f"New observations: {new_records}"
            )

            if new_records >= RETRAIN_AFTER:
                print("New observation threshold reached.")

                if run_pipeline():
                    last_count = get_metric_count()
                    print("ML pipeline updated successfully.")
                else:
                    print("Pipeline failed; it will retry on a later check.")

    except KeyboardInterrupt:
        print("\nContinuous ML pipeline stopped.")


if __name__ == "__main__":
    main()

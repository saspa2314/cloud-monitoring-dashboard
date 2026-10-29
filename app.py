import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection
from streamlit_autorefresh import st_autorefresh


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Cloud Infrastructure Monitoring Dashboard",
    page_icon="☁️",
    layout="wide"
)


# ==========================================================
# AUTO REFRESH
# ==========================================================

st_autorefresh(
    interval=5000,
    key="dashboard_refresh"
)


# ==========================================================
# TITLE
# ==========================================================

st.title("☁️ Cloud Infrastructure Monitoring Dashboard")

st.caption(
    "Real-time monitoring of Host System, Docker Containers "
    "and Kubernetes Workloads"
)

st.divider()


# ==========================================================
# DATABASE FUNCTION
# ==========================================================

def load_data(table_name):

    try:

        connection = get_connection()

        query = f"""
            SELECT *
            FROM {table_name}
            ORDER BY timestamp ASC
        """

        df = pd.read_sql(query, connection)

        connection.close()

        return df

    except Exception as e:

        st.error(f"Database error: {e}")

        return pd.DataFrame()


# ==========================================================
# LOAD DATA
# ==========================================================

system_df = load_data("system_metrics")

docker_df = load_data("docker_metrics")

kubernetes_df = load_data("kubernetes_metrics")


# ==========================================================
# HOST SYSTEM MONITORING
# ==========================================================

st.header("🖥️ Host System Monitoring")


if not system_df.empty:

    latest = system_df.iloc[-1]

    cpu = float(latest["cpu_usage"])

    memory = float(latest["memory_usage"])

    disk = float(latest["disk_usage"])


    # ------------------------------------------------------
    # STATUS FUNCTION
    # ------------------------------------------------------

    def get_status(value):

        if value >= 90:
            return "🔴 Critical"

        elif value >= 70:
            return "🟡 Warning"

        else:
            return "🟢 Normal"


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "CPU Usage",
            f"{cpu:.2f}%"
        )

        st.write(get_status(cpu))


    with col2:

        st.metric(
            "Memory Usage",
            f"{memory:.2f}%"
        )

        st.write(get_status(memory))


    with col3:

        st.metric(
            "Disk Usage",
            f"{disk:.2f}%"
        )

        st.write(get_status(disk))


    st.subheader("Host Resource Trends")


    col1, col2 = st.columns(2)


    with col1:

        fig_cpu = px.line(
            system_df,
            x="timestamp",
            y="cpu_usage",
            title="CPU Usage Over Time"
        )

        fig_cpu.update_layout(
            yaxis_title="CPU Usage (%)",
            xaxis_title="Time"
        )

        st.plotly_chart(
            fig_cpu,
            use_container_width=True
        )


    with col2:

        fig_memory = px.line(
            system_df,
            x="timestamp",
            y="memory_usage",
            title="Memory Usage Over Time"
        )

        fig_memory.update_layout(
            yaxis_title="Memory Usage (%)",
            xaxis_title="Time"
        )

        st.plotly_chart(
            fig_memory,
            use_container_width=True
        )


    fig_disk = px.line(
        system_df,
        x="timestamp",
        y="disk_usage",
        title="Disk Usage Over Time"
    )

    fig_disk.update_layout(
        yaxis_title="Disk Usage (%)",
        xaxis_title="Time"
    )

    st.plotly_chart(
        fig_disk,
        use_container_width=True
    )


    # ------------------------------------------------------
    # NETWORK
    # ------------------------------------------------------

    st.subheader("Network Activity")

    col1, col2 = st.columns(2)


    with col1:

        total_sent = system_df["bytes_sent"].iloc[-1]

        st.metric(
            "Data Sent",
            f"{total_sent / (1024 ** 2):.2f} MB"
        )


    with col2:

        total_received = system_df["bytes_received"].iloc[-1]

        st.metric(
            "Data Received",
            f"{total_received / (1024 ** 2):.2f} MB"
        )


else:

    st.warning("No host system data available.")


st.divider()


# ==========================================================
# DOCKER MONITORING
# ==========================================================

st.header("🐳 Docker Container Monitoring")


if not docker_df.empty:

    latest_docker = (
        docker_df
        .sort_values("timestamp")
        .groupby("container_id")
        .tail(1)
    )


    total_containers = len(latest_docker)

    running_containers = len(
        latest_docker[
            latest_docker["status"].str.lower() == "running"
        ]
    )

    stopped_containers = (
        total_containers - running_containers
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Total Containers",
            total_containers
        )


    with col2:

        st.metric(
            "Running",
            running_containers
        )


    with col3:

        st.metric(
            "Stopped",
            stopped_containers
        )


    st.subheader("Container Status")


    status_display = latest_docker[
        [
            "container_name",
            "status",
            "cpu_percent",
            "memory_usage_mb",
            "memory_percent"
        ]
    ].copy()


    st.dataframe(
        status_display,
        use_container_width=True,
        hide_index=True
    )


    # ------------------------------------------------------
    # DOCKER CPU
    # ------------------------------------------------------

    st.subheader("Docker CPU Usage")


    fig_docker_cpu = px.line(
        docker_df,
        x="timestamp",
        y="cpu_percent",
        color="container_name",
        title="Container CPU Usage"
    )

    fig_docker_cpu.update_layout(
        yaxis_title="CPU Usage (%)",
        xaxis_title="Time"
    )

    st.plotly_chart(
        fig_docker_cpu,
        use_container_width=True
    )


    # ------------------------------------------------------
    # DOCKER MEMORY
    # ------------------------------------------------------

    st.subheader("Docker Memory Usage")


    fig_docker_memory = px.line(
        docker_df,
        x="timestamp",
        y="memory_usage_mb",
        color="container_name",
        title="Container Memory Usage"
    )

    fig_docker_memory.update_layout(
        yaxis_title="Memory (MB)",
        xaxis_title="Time"
    )

    st.plotly_chart(
        fig_docker_memory,
        use_container_width=True
    )


    # ------------------------------------------------------
    # DOCKER NETWORK
    # ------------------------------------------------------

    st.subheader("Docker Network Activity")


    col1, col2 = st.columns(2)


    with col1:

        fig_received = px.line(
            docker_df,
            x="timestamp",
            y="network_received_mb",
            color="container_name",
            title="Network Received"
        )

        fig_received.update_layout(
            yaxis_title="MB",
            xaxis_title="Time"
        )

        st.plotly_chart(
            fig_received,
            use_container_width=True
        )


    with col2:

        fig_sent = px.line(
            docker_df,
            x="timestamp",
            y="network_sent_mb",
            color="container_name",
            title="Network Sent"
        )

        fig_sent.update_layout(
            yaxis_title="MB",
            xaxis_title="Time"
        )

        st.plotly_chart(
            fig_sent,
            use_container_width=True
        )


else:

    st.warning("No Docker metrics available.")


st.divider()


# ==========================================================
# KUBERNETES MONITORING
# ==========================================================

st.header("☸️ Kubernetes Monitoring")


if not kubernetes_df.empty:

    # ------------------------------------------------------
    # LATEST DATA FOR EACH POD
    # ------------------------------------------------------

    latest_kubernetes = (
        kubernetes_df
        .sort_values("timestamp")
        .groupby("pod_name")
        .tail(1)
        .copy()
    )


    # ------------------------------------------------------
    # BASIC STATISTICS
    # ------------------------------------------------------

    total_pods = len(latest_kubernetes)

    running_pods = len(
        latest_kubernetes[
            latest_kubernetes["status"].str.lower() == "running"
        ]
    )

    non_running_pods = (
        total_pods - running_pods
    )

    node_count = (
        latest_kubernetes["node_name"]
        .nunique()
    )


    # ------------------------------------------------------
    # POD CARDS
    # ------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Total Pods",
            total_pods
        )


    with col2:

        st.metric(
            "Running Pods",
            running_pods
        )


    with col3:

        st.metric(
            "Non-Running Pods",
            non_running_pods
        )


    with col4:

        st.metric(
            "Kubernetes Nodes",
            node_count
        )


    # ------------------------------------------------------
    # ACTUAL RESOURCE USAGE
    # ------------------------------------------------------

    st.subheader("Kubernetes Resource Utilization")


    total_cpu = (
        latest_kubernetes[
            "cpu_usage_millicores"
        ]
        .fillna(0)
        .sum()
    )


    total_memory = (
        latest_kubernetes[
            "memory_usage_mb"
        ]
        .fillna(0)
        .sum()
    )


    col1, col2 = st.columns(2)


    with col1:

        st.metric(
            "Total CPU Usage",
            f"{total_cpu:.2f} m"
        )


    with col2:

        st.metric(
            "Total Memory Usage",
            f"{total_memory:.2f} MB"
        )


    # ------------------------------------------------------
    # POD STATUS TABLE
    # ------------------------------------------------------

    st.subheader("Pod Status")


    pod_columns = [
        "pod_name",
        "node_name",
        "namespace",
        "status",
        "cpu_request",
        "cpu_limit",
        "cpu_usage_millicores",
        "memory_request",
        "memory_limit",
        "memory_usage_mb"
    ]


    available_columns = [
        column
        for column in pod_columns
        if column in latest_kubernetes.columns
    ]


    st.dataframe(
        latest_kubernetes[
            available_columns
        ],
        use_container_width=True,
        hide_index=True
    )


    # ------------------------------------------------------
    # CPU USAGE BY POD
    # ------------------------------------------------------

    st.subheader("CPU Usage by Pod")


    fig_pod_cpu = px.bar(
        latest_kubernetes,
        x="pod_name",
        y="cpu_usage_millicores",
        title="Current CPU Usage by Kubernetes Pod"
    )

    fig_pod_cpu.update_layout(
        xaxis_title="Pod",
        yaxis_title="CPU (millicores)"
    )


    st.plotly_chart(
        fig_pod_cpu,
        use_container_width=True
    )


    # ------------------------------------------------------
    # MEMORY USAGE BY POD
    # ------------------------------------------------------

    st.subheader("Memory Usage by Pod")


    fig_pod_memory = px.bar(
        latest_kubernetes,
        x="pod_name",
        y="memory_usage_mb",
        title="Current Memory Usage by Kubernetes Pod"
    )

    fig_pod_memory.update_layout(
        xaxis_title="Pod",
        yaxis_title="Memory (MB)"
    )


    st.plotly_chart(
        fig_pod_memory,
        use_container_width=True
    )


    # ------------------------------------------------------
    # CPU TREND
    # ------------------------------------------------------

    st.subheader("Kubernetes CPU Usage Trend")


    fig_k8s_cpu = px.line(
        kubernetes_df,
        x="timestamp",
        y="cpu_usage_millicores",
        color="pod_name",
        title="CPU Usage Over Time"
    )


    fig_k8s_cpu.update_layout(
        xaxis_title="Time",
        yaxis_title="CPU (millicores)"
    )


    st.plotly_chart(
        fig_k8s_cpu,
        use_container_width=True
    )


    # ------------------------------------------------------
    # MEMORY TREND
    # ------------------------------------------------------

    st.subheader("Kubernetes Memory Usage Trend")


    fig_k8s_memory = px.line(
        kubernetes_df,
        x="timestamp",
        y="memory_usage_mb",
        color="pod_name",
        title="Memory Usage Over Time"
    )


    fig_k8s_memory.update_layout(
        xaxis_title="Time",
        yaxis_title="Memory (MB)"
    )


    st.plotly_chart(
        fig_k8s_memory,
        use_container_width=True
    )


    # ------------------------------------------------------
    # POD STATUS CHART
    # ------------------------------------------------------

    st.subheader("Pod Status Distribution")


    status_counts = (
        latest_kubernetes["status"]
        .value_counts()
        .reset_index()
    )


    status_counts.columns = [
        "status",
        "count"
    ]


    fig_status = px.bar(
        status_counts,
        x="status",
        y="count",
        title="Kubernetes Pod Status"
    )


    st.plotly_chart(
        fig_status,
        use_container_width=True
    )


    # ------------------------------------------------------
    # PODS PER NODE
    # ------------------------------------------------------

    st.subheader("Pods per Kubernetes Node")


    pods_per_node = (
        latest_kubernetes["node_name"]
        .value_counts()
        .reset_index()
    )


    pods_per_node.columns = [
        "node_name",
        "pod_count"
    ]


    fig_nodes = px.bar(
        pods_per_node,
        x="node_name",
        y="pod_count",
        title="Pods Running on Each Node"
    )


    st.plotly_chart(
        fig_nodes,
        use_container_width=True
    )


else:

    st.warning(
        "No Kubernetes metrics available. "
        "Make sure kubernetes_monitor.py is running."
    )


st.divider()


# ==========================================================
# RAW DATA
# ==========================================================

with st.expander("📊 View Raw Host Data"):

    if not system_df.empty:

        st.dataframe(
            system_df.tail(100),
            use_container_width=True,
            hide_index=True
        )


with st.expander("🐳 View Raw Docker Data"):

    if not docker_df.empty:

        st.dataframe(
            docker_df.tail(100),
            use_container_width=True,
            hide_index=True
        )


with st.expander("☸️ View Raw Kubernetes Data"):

    if not kubernetes_df.empty:

        st.dataframe(
            kubernetes_df.tail(100),
            use_container_width=True,
            hide_index=True
        )


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

st.caption(
    "Cloud Infrastructure Monitoring Dashboard | "
    "Python + SQL Server + Docker + Kubernetes + Streamlit + Power BI"
)

# ============================================================
# ML ANOMALY DETECTION & INFRASTRUCTURE HEALTH
# ============================================================

st.header("🤖 ML Anomaly Detection & Infrastructure Health")

conn = get_connection()

try:
    # Component health summary
    health_df = pd.read_sql_query(
        """
        SELECT
            component_name,
            records_analyzed,
            anomaly_count,
            anomaly_rate,
            health_score,
            health_status,
            status_message,
            timestamp
        FROM component_health
        """,
        conn
    )

    # Recent system anomalies
    system_anomaly_df = pd.read_sql_query(
        """
        SELECT TOP 20
            timestamp,
            cpu_usage,
            memory_usage,
            disk_usage,
            anomaly_score,
            anomaly_status
        FROM system_anomalies
        ORDER BY timestamp DESC
        """,
        conn
    )

    # Recent Docker anomalies
    docker_anomaly_df = pd.read_sql_query(
        """
        SELECT TOP 20
            timestamp,
            container_name,
            cpu_percent,
            memory_usage_mb,
            network_received_mb,
            anomaly_score,
            anomaly_status
        FROM docker_anomalies
        ORDER BY timestamp DESC
        """,
        conn
    )

    # Recent Kubernetes anomalies
    k8s_anomaly_df = pd.read_sql_query(
        """
        SELECT TOP 20
            timestamp,
            pod_name,
            namespace,
            cpu_usage_millicores,
            memory_usage_mb,
            anomaly_score,
            anomaly_status
        FROM kubernetes_anomalies
        ORDER BY timestamp DESC
        """,
        conn
    )

finally:
    conn.close()


if not health_df.empty:
    st.subheader("Component Health")

    # Display the most recent health record per component.
    health_df["timestamp"] = pd.to_datetime(health_df["timestamp"])
    health_df = health_df.sort_values("timestamp")
    latest_health = health_df.groupby(
        "component_name", as_index=False
    ).tail(1)

    col1, col2, col3 = st.columns(3)

    for col, component in zip(
        [col1, col2, col3],
        ["System", "Docker", "Kubernetes"]
    ):
        row = latest_health[
            latest_health["component_name"] == component
        ]

        with col:
            st.markdown(f"**{component}**")
            if not row.empty:
                item = row.iloc[0]
                score = item["health_score"]

                if pd.notna(score):
                    st.metric("Health Score", f"{score:.1f}/100")
                else:
                    st.metric("Health Score", "Unavailable")

                st.write(f"Status: {item['health_status']}")
                st.write(
                    f"Anomalies: {item['anomaly_count']} / "
                    f"{item['records_analyzed']}"
                )
            else:
                st.info("No health assessment available.")

    st.dataframe(latest_health, use_container_width=True)

else:
    st.info("No component health results found. Run the ML pipeline first.")


st.subheader("System Anomaly History")

if not system_anomaly_df.empty:
    system_anomaly_df["timestamp"] = pd.to_datetime(
        system_anomaly_df["timestamp"]
    )

    st.plotly_chart(
        px.scatter(
            system_anomaly_df,
            x="timestamp",
            y="cpu_usage",
            color="anomaly_status",
            hover_data=["memory_usage", "disk_usage", "anomaly_score"],
            title="Host CPU Usage and Detected Anomalies"
        ),
        use_container_width=True
    )

    st.dataframe(system_anomaly_df, use_container_width=True)
else:
    st.info("No system anomaly records found.")


st.subheader("Docker Anomalies")

if not docker_anomaly_df.empty:
    st.dataframe(docker_anomaly_df, use_container_width=True)
else:
    st.info("No Docker anomaly records found.")


st.subheader("Kubernetes Anomalies")

if not k8s_anomaly_df.empty:
    st.dataframe(k8s_anomaly_df, use_container_width=True)
else:
    st.info("No Kubernetes anomaly records found.")


@echo off

echo ========================================
echo Cloud Infrastructure Monitoring System
echo ========================================

echo.
echo Starting System Monitor...
start "System Monitor" cmd /k "python monitor.py"

echo Starting Docker Monitor...
start "Docker Monitor" cmd /k "python docker_monitor.py"

echo Starting Kubernetes Monitor...
start "Kubernetes Monitor" cmd /k "python kubernetes_monitor.py"

echo Starting Continuous ML Pipeline...
start "ML Pipeline" cmd /k "python ml_pipeline.py"

echo Starting Streamlit Dashboard...
start "Streamlit Dashboard" cmd /k "streamlit run app.py"

echo.
echo ========================================
echo All services started!
echo ========================================
pause

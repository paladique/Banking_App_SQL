import subprocess
import time
import sys

def run_services():
    """Launch both services"""
    try:
        # Start analytics service first
        analytics_process = subprocess.Popen([sys.executable, "agent_analytics.py"])
        print("[1] Analytics service started")

        time.sleep(2)  # Give analytics service time to start
        
        # Start banking service
        banking_process = subprocess.Popen([sys.executable, "banking_app.py"])
        print("[2] Banking service started")
        
        print("\nBoth services are running!")
        print("Banking App: http://127.0.0.1:5001/")
        print("Analytics Service: http://127.0.0.1:5002/")
        print("\nPress Ctrl+C to stop both services...")
        
        # Wait for processes
        banking_process.wait()
        analytics_process.wait()
        
    except KeyboardInterrupt:
        print("\nShutting down services...")
        analytics_process.terminate()
        banking_process.terminate()

if __name__ == '__main__':
    run_services()
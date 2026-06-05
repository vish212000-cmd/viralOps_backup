import subprocess
import socket
import time
import sys
import os

def is_server_ready(port, timeout=45):
    """Wait for server to be ready by polling the port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('localhost', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.5)
    return False

def kill_process_tree(pid):
    """Cleanly terminate the process tree on Windows."""
    try:
        subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Failed to taskkill PID {pid}: {e}")

def main():
    print("=== STARTING SERVER LIFECYCLE MANAGER ===")
    
    # Setup log files
    backend_log = open("backend_server.log", "w")
    frontend_log = open("frontend_server.log", "w")
    
    # Port 8000: Django Backend
    print("Starting Django Backend Server on port 8000...")
    backend_proc = subprocess.Popen(
        "venv\\Scripts\\python.exe manage.py runserver 8000",
        shell=True,
        stdout=backend_log,
        stderr=backend_log
    )
    
    # Port 5173: Vite Frontend
    print("Starting Vite Frontend Server on port 5173...")
    frontend_proc = subprocess.Popen(
        "npm run dev -- --port 5173",
        shell=True,
        cwd="..\\frontend",
        stdout=frontend_log,
        stderr=frontend_log
    )
    
    ret_code = 1
    try:
        print("Waiting for Django Backend (port 8000)...")
        if not is_server_ready(8000):
            raise RuntimeError("Backend failed to start on port 8000")
        print("Django Backend ready!")
        
        print("Waiting for Vite Frontend (port 5173)...")
        if not is_server_ready(5173):
            raise RuntimeError("Frontend failed to start on port 5173")
        print("Vite Frontend ready!")
        
        print("Running Playwright E2E User Validation...")
        result = subprocess.run("venv\\Scripts\\python.exe run_e2e_validation.py", shell=True)
        ret_code = result.returncode
        print(f"Playwright E2E Validation completed with code: {ret_code}")
        
    except Exception as e:
        print(f"Error during E2E validation: {e}")
        ret_code = 1
        
    finally:
        print("Stopping backend and frontend servers...")
        kill_process_tree(backend_proc.pid)
        kill_process_tree(frontend_proc.pid)
        backend_log.close()
        frontend_log.close()
        print("Servers stopped cleanly.")
        
    sys.exit(ret_code)

if __name__ == '__main__':
    main()

"""
Enhanced Server Manager for Integration Tests.

Provides comprehensive logging and monitoring for Flask backend and Vite frontend servers.
"""

import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests


class ServerLogCapture:
    """Captures and stores server logs with thread-safe access."""

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.logs: List[str] = []
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f"ServerLogCapture.{server_name}")

    def add_log(self, line: str):
        """Add a log line with timestamp."""
        timestamp = time.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
        formatted_line = f"[{timestamp}] {self.server_name}: {line.strip()}"

        with self.lock:
            self.logs.append(formatted_line)

        # Also log to pytest output for immediate visibility
        self.logger.info(formatted_line)

    def get_logs(self) -> List[str]:
        """Get all captured logs."""
        with self.lock:
            return self.logs.copy()

    def get_recent_logs(self, count: int = 10) -> List[str]:
        """Get the most recent logs."""
        with self.lock:
            return self.logs[-count:]

    def dump_logs(self) -> str:
        """Get all logs as a single string."""
        with self.lock:
            return "\n".join(self.logs)


class LogStreamReader:
    """Reads from a subprocess stream and captures logs."""

    def __init__(self, stream, log_capture: ServerLogCapture):
        self.stream = stream
        self.log_capture = log_capture
        self.thread = None
        self.running = False

    def start(self):
        """Start reading from the stream."""
        self.running = True
        self.thread = threading.Thread(target=self._read_stream, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop reading from the stream."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _read_stream(self):
        """Read lines from the stream and capture them."""
        try:
            for line in iter(self.stream.readline, ""):
                if not self.running:
                    break
                if line:
                    self.log_capture.add_log(line)
        except Exception as e:
            self.log_capture.add_log(f"Log reader error: {e}")


class EnhancedServerManager:
    """Enhanced server manager with comprehensive logging and monitoring."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.flask_process = None
        self.vite_process = None
        self.flask_port = 5000
        self.vite_port = 3001
        self.flask_url = f"http://localhost:{self.flask_port}"
        self.vite_url = f"http://localhost:{self.vite_port}"

        # Logging infrastructure
        self.flask_logs = ServerLogCapture("Flask")
        self.vite_logs = ServerLogCapture("Vite")
        self.flask_log_reader = None
        self.vite_log_reader = None

        # Setup logging
        self.logger = logging.getLogger("EnhancedServerManager")

    def start_flask(self, db_path: Optional[str] = None) -> bool:
        """Start Flask backend server with comprehensive logging."""
        try:
            self.logger.info("Starting Flask backend server...")

            # Prepare environment
            env = os.environ.copy()
            env["FLASK_ENV"] = "testing"
            env["FLASK_DEBUG"] = "1"  # Enable debug for better logging
            env["PYTHONUNBUFFERED"] = "1"  # Ensure logs are flushed immediately

            if db_path:
                env["DATABASE_URL"] = f"sqlite:///{db_path}"
                env["TESTING"] = "true"

            # Start Flask process
            cmd = f"cd {self.project_root} && eval $(poetry env activate) && python run.py"
            self.flask_process = subprocess.Popen(
                cmd,
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Start log capture
            self.flask_log_reader = LogStreamReader(
                self.flask_process.stdout, self.flask_logs
            )
            self.flask_log_reader.start()

            # Wait for Flask to be ready
            self.logger.info("Waiting for Flask to become ready...")
            for attempt in range(30):  # 30 second timeout
                try:
                    response = requests.get(self.flask_url, timeout=2)
                    if response.status_code in [
                        200,
                        302,
                        404,
                    ]:  # Any valid HTTP response
                        self.logger.info(
                            f"✓ Flask server ready at {self.flask_url} (status: {response.status_code})"
                        )
                        return True
                except requests.exceptions.RequestException as e:
                    self.logger.debug(
                        f"Flask not ready yet (attempt {attempt + 1}): {e}"
                    )

                time.sleep(1)

            self.logger.error("Flask server failed to become ready within 30 seconds")
            self._dump_server_logs()
            return False

        except Exception as e:
            self.logger.error(f"Failed to start Flask server: {e}")
            self._dump_server_logs()
            return False

    def start_vite(self) -> bool:
        """Start Vite frontend server with comprehensive logging."""
        try:
            self.logger.info("Starting Vite frontend server...")

            frontend_dir = self.project_root / "frontend"
            if not frontend_dir.exists():
                self.logger.error("Frontend directory not found")
                return False

            # Prepare environment
            env = os.environ.copy()
            env["NODE_ENV"] = "development"

            # Start Vite process with integration test config for enhanced logging
            cmd = f"cd {frontend_dir} && npm run dev -- --config vite.config.integration.ts --port {self.vite_port} --host 0.0.0.0"
            self.vite_process = subprocess.Popen(
                cmd,
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Start log capture
            self.vite_log_reader = LogStreamReader(
                self.vite_process.stdout, self.vite_logs
            )
            self.vite_log_reader.start()

            # Wait for Vite to be ready
            self.logger.info("Waiting for Vite to become ready...")
            for attempt in range(30):  # 30 second timeout
                try:
                    response = requests.get(self.vite_url, timeout=2)
                    if response.status_code == 200:
                        self.logger.info(f"✓ Vite server ready at {self.vite_url}")
                        return True
                except requests.exceptions.RequestException as e:
                    self.logger.debug(
                        f"Vite not ready yet (attempt {attempt + 1}): {e}"
                    )

                time.sleep(1)

            self.logger.error("Vite server failed to become ready within 30 seconds")
            self._dump_server_logs()
            return False

        except Exception as e:
            self.logger.error(f"Failed to start Vite server: {e}")
            self._dump_server_logs()
            return False

    def start_servers(self, db_path: Optional[str] = None) -> bool:
        """Start both servers with enhanced error handling."""
        self.logger.info("Starting Flask and Vite servers for integration tests...")

        # Start Flask first
        if not self.start_flask(db_path):
            self.logger.error("Failed to start Flask server")
            return False

        # Start Vite second
        if not self.start_vite():
            self.logger.error("Failed to start Vite server")
            self.stop_servers()
            return False

        self.logger.info("✓ Both servers started successfully")
        self._log_server_status()
        return True

    def stop_servers(self):
        """Stop both servers with proper cleanup."""
        self.logger.info("Stopping servers...")

        # Stop log readers first
        if self.flask_log_reader:
            self.flask_log_reader.stop()
        if self.vite_log_reader:
            self.vite_log_reader.stop()

        # Stop Flask
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process.wait(timeout=5)
                self.logger.info("✓ Flask server stopped")
            except subprocess.TimeoutExpired:
                self.logger.warning("Flask server didn't terminate, killing...")
                self.flask_process.kill()
                self.flask_process.wait()
            except Exception as e:
                self.logger.error(f"Error stopping Flask: {e}")

        # Stop Vite
        if self.vite_process:
            try:
                self.vite_process.terminate()
                self.vite_process.wait(timeout=5)
                self.logger.info("✓ Vite server stopped")
            except subprocess.TimeoutExpired:
                self.logger.warning("Vite server didn't terminate, killing...")
                self.vite_process.kill()
                self.vite_process.wait()
            except Exception as e:
                self.logger.error(f"Error stopping Vite: {e}")

    def health_check(self) -> Dict[str, bool]:
        """Check health of both servers."""
        flask_healthy = False
        vite_healthy = False

        try:
            response = requests.get(self.flask_url, timeout=2)
            flask_healthy = response.status_code in [200, 302, 404]
        except Exception:
            pass

        try:
            response = requests.get(self.vite_url, timeout=2)
            vite_healthy = response.status_code == 200
        except Exception:
            pass

        return {"flask": flask_healthy, "vite": vite_healthy}

    def get_server_urls(self) -> Dict[str, str]:
        """Get server URLs."""
        return {"flask_url": self.flask_url, "vite_url": self.vite_url}

    def _log_server_status(self):
        """Log current server status."""
        health = self.health_check()
        self.logger.info(
            f"Server status - Flask: {'✓' if health['flask'] else '✗'}, Vite: {'✓' if health['vite'] else '✗'}"
        )

    def _dump_server_logs(self):
        """Dump server logs for debugging."""
        self.logger.info("=== FLASK SERVER LOGS ===")
        flask_logs = self.flask_logs.get_logs()
        if flask_logs:
            for log in flask_logs[-20:]:  # Last 20 lines
                self.logger.info(log)
        else:
            self.logger.info("No Flask logs available")

        self.logger.info("=== VITE SERVER LOGS ===")
        vite_logs = self.vite_logs.get_logs()
        if vite_logs:
            for log in vite_logs[-20:]:  # Last 20 lines
                self.logger.info(log)
        else:
            self.logger.info("No Vite logs available")

    def get_flask_logs(self) -> List[str]:
        """Get Flask server logs."""
        return self.flask_logs.get_logs()

    def get_vite_logs(self) -> List[str]:
        """Get Vite server logs."""
        return self.vite_logs.get_logs()

    def save_logs_to_file(self, filepath: str, append: bool = False):
        """Save all server logs to a file."""
        try:
            mode = "a" if append else "w"
            with open(filepath, mode) as f:
                if not append:
                    f.write("=== INTEGRATION TEST SERVER LOGS ===\n\n")
                else:
                    f.write(f"\n=== LOGS UPDATE AT {time.strftime('%H:%M:%S')} ===\n")

                f.write("=== FLASK SERVER LOGS ===\n")
                flask_logs = self.flask_logs.get_logs()
                if flask_logs:
                    for log in flask_logs:
                        f.write(f"{log}\n")
                else:
                    f.write("No Flask logs captured\n")

                f.write("\n=== VITE SERVER LOGS ===\n")
                vite_logs = self.vite_logs.get_logs()
                if vite_logs:
                    for log in vite_logs:
                        f.write(f"{log}\n")
                else:
                    f.write("No Vite logs captured\n")

                f.write("\n=== END OF LOGS ===\n")

            self.logger.info(f"Server logs saved to {filepath} (append={append})")
        except Exception as e:
            self.logger.error(f"Failed to save logs to {filepath}: {e}")

    def mark_test_start(self, test_name: str) -> None:
        """Mark the start of a test in the logs."""
        # Add marker to both log streams
        self.flask_logs.add_log(f"TEST_MARKER: Starting test {test_name}")
        self.vite_logs.add_log(f"TEST_MARKER: Starting test {test_name}")

        self.logger.info(f"Test marker added: {test_name}")

    def mark_test_end(self, test_name: str, status: str = "completed") -> None:
        """Mark the end of a test in the logs."""
        # Add marker to both log streams
        self.flask_logs.add_log(f"TEST_MARKER: Finished test {test_name} ({status})")
        self.vite_logs.add_log(f"TEST_MARKER: Finished test {test_name} ({status})")

        self.logger.info(f"Test marker added: {test_name} finished ({status})")

"""
Managed Process for experiment orchestration.

Handles lifecycle of routing daemon and GRU server with:
- Health check polling
- Graceful shutdown
- PID file management
- Context manager support
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class ProcessConfig:
    """Configuration for a managed process."""
    name: str
    command: List[str]
    health_url: Optional[str] = None
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    log_dir: Optional[Path] = None
    health_timeout: int = 30
    health_interval: float = 0.5
    shutdown_timeout: int = 10


class ManagedProcess:
    """
    Managed subprocess with health checking and graceful shutdown.
    
    Usage:
        config = ProcessConfig(
            name="daemon",
            command=["uv", "run", "python", "-m", "daemon.routing_daemon"],
            health_url="http://localhost:9104/health",
        )
        
        with ManagedProcess(config) as proc:
            proc.wait_healthy()
            # run experiment
        # automatic cleanup
    """
    
    def __init__(self, config: ProcessConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.pid_file: Optional[Path] = None
        self.log_file: Optional[Path] = None
        self._stdout_file = None
        self._stderr_file = None
    
    def start(self) -> "ManagedProcess":
        """Start the subprocess."""
        if self.process is not None:
            raise RuntimeError(f"Process {self.config.name} already started")
        
        # Setup logging
        if self.config.log_dir:
            self.config.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.config.log_dir / f"{self.config.name}.log"
            self._stdout_file = open(self.log_file, "w")
            self._stderr_file = subprocess.STDOUT
        else:
            self._stdout_file = subprocess.DEVNULL
            self._stderr_file = subprocess.DEVNULL
        
        # Build environment
        env = os.environ.copy()
        if self.config.env:
            env.update(self.config.env)
        
        logger.info(
            "Starting managed process",
            name=self.config.name,
            command=" ".join(self.config.command),
            cwd=self.config.cwd,
        )
        
        self.process = subprocess.Popen(
            self.config.command,
            stdout=self._stdout_file,
            stderr=self._stderr_file,
            cwd=self.config.cwd,
            env=env,
            start_new_session=True,  # Detach from terminal
        )
        
        # Write PID file
        if self.config.log_dir:
            self.pid_file = self.config.log_dir / f"{self.config.name}.pid"
            self.pid_file.write_text(str(self.process.pid))
        
        logger.info(
            "Process started",
            name=self.config.name,
            pid=self.process.pid,
        )
        
        return self
    
    def wait_healthy(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for process to become healthy.
        
        Args:
            timeout: Override default health timeout
            
        Returns:
            True if healthy, raises exception on timeout
        """
        if not self.config.health_url:
            logger.warning("No health URL configured, skipping health check", name=self.config.name)
            return True
        
        timeout = timeout or self.config.health_timeout
        start_time = time.time()
        last_error = None
        
        logger.info(
            "Waiting for process health",
            name=self.config.name,
            health_url=self.config.health_url,
            timeout=timeout,
        )
        
        while time.time() - start_time < timeout:
            # Check if process died
            if self.process and self.process.poll() is not None:
                raise RuntimeError(
                    f"Process {self.config.name} died with code {self.process.returncode}"
                )
            
            try:
                with httpx.Client(timeout=2.0) as client:
                    response = client.get(self.config.health_url)
                    if response.status_code == 200:
                        elapsed = time.time() - start_time
                        logger.info(
                            "Process healthy",
                            name=self.config.name,
                            elapsed_sec=round(elapsed, 2),
                        )
                        return True
            except Exception as e:
                last_error = e
            
            time.sleep(self.config.health_interval)
        
        raise TimeoutError(
            f"Process {self.config.name} not healthy after {timeout}s: {last_error}"
        )
    
    def stop(self, timeout: Optional[int] = None) -> int:
        """
        Stop the process gracefully.
        
        Args:
            timeout: Override default shutdown timeout
            
        Returns:
            Process exit code
        """
        if self.process is None:
            return 0
        
        timeout = timeout or self.config.shutdown_timeout
        
        # Check if already dead
        if self.process.poll() is not None:
            return self._cleanup()
        
        logger.info(
            "Stopping process",
            name=self.config.name,
            pid=self.process.pid,
            timeout=timeout,
        )
        
        # Send SIGTERM
        try:
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
        except ProcessLookupError:
            return self._cleanup()
        
        # Wait for graceful shutdown
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(
                "Process did not stop gracefully, sending SIGKILL",
                name=self.config.name,
                pid=self.process.pid,
            )
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                self.process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
        
        return self._cleanup()
    
    def _cleanup(self) -> int:
        """Clean up resources and return exit code."""
        exit_code = self.process.returncode if self.process else 0
        
        # Close log files
        if self._stdout_file and self._stdout_file != subprocess.DEVNULL:
            self._stdout_file.close()
        
        # Remove PID file
        if self.pid_file and self.pid_file.exists():
            self.pid_file.unlink()
        
        logger.info(
            "Process stopped",
            name=self.config.name,
            exit_code=exit_code,
        )
        
        self.process = None
        return exit_code
    
    def is_running(self) -> bool:
        """Check if process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def __enter__(self) -> "ManagedProcess":
        """Context manager entry - starts process."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - stops process."""
        self.stop()
        return False  # Don't suppress exceptions


class ProcessManager:
    """
    Manages multiple processes for experiment orchestration.
    
    Usage:
        manager = ProcessManager(log_dir=Path("results/run-001"))
        
        with manager:
            manager.start_gru(gru_port=8090)
            manager.start_daemon(scenario="s4-hybrid-predictive")
            # run experiment
        # all processes cleaned up
    """
    
    def __init__(self, log_dir: Path, controller_dir: Path):
        self.log_dir = log_dir
        self.controller_dir = controller_dir
        self.processes: Dict[str, ManagedProcess] = {}
    
    def start_daemon(
        self,
        scenario: str,
        prometheus_url: str = None,
        haproxy_host: str = "localhost",
        haproxy_port: int = 19999,
        interval: int = 10,
        api_port: int = 9104,
        gru_url: Optional[str] = None,
    ) -> ManagedProcess:
        """Start the routing daemon."""
        # Use settings default if not provided
        prometheus_url = prometheus_url or settings.PROMETHEUS_URL
        
        cmd = [
            "uv", "run", "python", "-m", "daemon.routing_daemon",
            "--scenario", scenario,
            "--prometheus-url", prometheus_url,
            "--haproxy-host", haproxy_host,
            "--haproxy-port", str(haproxy_port),
            "--interval", str(interval),
            "--api-port", str(api_port),
        ]
        
        if gru_url:
            cmd.extend(["--gru-url", gru_url])
        
        config = ProcessConfig(
            name="routing-daemon",
            command=cmd,
            health_url=f"http://localhost:{api_port}/health",
            cwd=str(self.controller_dir),
            log_dir=self.log_dir,
            health_timeout=30,
        )
        
        proc = ManagedProcess(config)
        proc.start()
        self.processes["daemon"] = proc
        return proc
    
    def start_gru(
        self,
        port: int = 8090,
        model_path: Optional[str] = None,
    ) -> ManagedProcess:
        """Start the GRU prediction server."""
        cmd = [
            "uv", "run", "python", "-m", "daemon.gru_server",
            "--port", str(port),
        ]
        
        if model_path:
            cmd.extend(["--model", model_path])
        
        config = ProcessConfig(
            name="gru-server",
            command=cmd,
            health_url=f"http://localhost:{port}/health",
            cwd=str(self.controller_dir),
            log_dir=self.log_dir,
            health_timeout=60,  # Model loading can be slow
        )
        
        proc = ManagedProcess(config)
        proc.start()
        self.processes["gru"] = proc
        return proc
    
    def stop_all(self) -> None:
        """Stop all managed processes."""
        for name, proc in reversed(list(self.processes.items())):
            try:
                proc.stop()
            except Exception as e:
                logger.error("Failed to stop process", name=name, error=str(e))
        self.processes.clear()
    
    def __enter__(self) -> "ProcessManager":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop_all()
        return False

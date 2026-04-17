from __future__ import annotations

import re
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, Optional

from app.config import settings

REMOTE_ADDR_RE = re.compile(r"(?P<host>[a-zA-Z0-9.-]+):(?P<port>\d{2,5})")


@dataclass
class BoreTunnelState:
    local_port: int
    server: str
    desired: bool = True
    running: bool = False
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    restart_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_exit_code: Optional[int] = None
    last_error: Optional[str] = None
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=200))
    process: Optional[subprocess.Popen[str]] = None
    monitor_thread: Optional[threading.Thread] = None

    def to_dict(self) -> dict:
        return {
            "local_port": self.local_port,
            "server": self.server,
            "desired": self.desired,
            "running": self.running,
            "remote_host": self.remote_host,
            "remote_port": self.remote_port,
            "restart_count": self.restart_count,
            "started_at": self.started_at.isoformat() + "Z",
            "last_exit_code": self.last_exit_code,
            "last_error": self.last_error,
            "last_logs": list(self.logs)[-20:],
        }


class BoreManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tunnels: Dict[int, BoreTunnelState] = {}

    def start_tunnel(self, local_port: int, server: Optional[str] = None) -> BoreTunnelState:
        target_server = server or settings.bore_server
        with self._lock:
            state = self._tunnels.get(local_port)
            if state and state.desired and state.running:
                return state
            if state is None:
                state = BoreTunnelState(local_port=local_port, server=target_server)
                self._tunnels[local_port] = state
            else:
                state.server = target_server
                state.desired = True
                state.last_error = None

            self._spawn_locked(state)
            return state

    def stop_tunnel(self, local_port: int) -> BoreTunnelState:
        with self._lock:
            state = self._tunnels.get(local_port)
            if state is None:
                raise ValueError(f"no bore tunnel found for local port {local_port}")
            state.desired = False
            proc = state.process

        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)

        with self._lock:
            state.running = False
            state.process = None
            return state

    def list_tunnels(self) -> list[dict]:
        with self._lock:
            return [state.to_dict() for _, state in sorted(self._tunnels.items())]

    def _spawn_locked(self, state: BoreTunnelState) -> None:
        cmd = [settings.bore_binary, "local", str(state.local_port), "--to", state.server]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            state.running = False
            state.last_error = f"bore binary not found: {settings.bore_binary}"
            raise RuntimeError(state.last_error) from exc
        except Exception as exc:  # pragma: no cover - defensive branch
            state.running = False
            state.last_error = f"failed to start bore: {exc}"
            raise RuntimeError(state.last_error) from exc

        state.process = process
        state.running = True
        state.started_at = datetime.utcnow()
        state.logs.append(f"spawned: {' '.join(cmd)}")

        monitor = threading.Thread(target=self._monitor, args=(state.local_port,), daemon=True)
        state.monitor_thread = monitor
        monitor.start()

    def _monitor(self, local_port: int) -> None:
        while True:
            with self._lock:
                state = self._tunnels.get(local_port)
                if state is None:
                    return
                proc = state.process
                desired = state.desired

            if proc is None:
                return

            if proc.stdout is not None:
                for line in proc.stdout:
                    clean = line.strip()
                    if not clean:
                        continue
                    with self._lock:
                        current = self._tunnels.get(local_port)
                        if current is None:
                            return
                        current.logs.append(clean)
                        self._parse_remote_addr_locked(current, clean)

            exit_code = proc.wait()
            with self._lock:
                current = self._tunnels.get(local_port)
                if current is None:
                    return
                current.running = False
                current.process = None
                current.last_exit_code = exit_code
                should_restart = current.desired
                if not should_restart:
                    current.logs.append("stopped by request")
                else:
                    current.restart_count += 1
                    current.logs.append(f"exited with code {exit_code}, restarting")

            if not desired or not should_restart:
                return

            time.sleep(max(1, settings.bore_restart_backoff_seconds))
            with self._lock:
                current = self._tunnels.get(local_port)
                if current is None or not current.desired:
                    return
                try:
                    self._spawn_locked(current)
                except RuntimeError as exc:
                    current.last_error = str(exc)
                    return
                return

    def _parse_remote_addr_locked(self, state: BoreTunnelState, line: str) -> None:
        lowered = line.lower()
        if "listening" not in lowered and "remote" not in lowered and "forward" not in lowered:
            return
        for match in REMOTE_ADDR_RE.finditer(line):
            host = match.group("host")
            port = int(match.group("port"))
            if port == state.local_port:
                continue
            state.remote_host = host
            state.remote_port = port


_bore_manager: Optional[BoreManager] = None


def get_bore_manager() -> BoreManager:
    global _bore_manager
    if _bore_manager is None:
        _bore_manager = BoreManager()
    return _bore_manager

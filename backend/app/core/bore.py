from __future__ import annotations

import re
import shlex
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Deque, Dict, Optional

from app.config import runtime_state, settings

REMOTE_ADDR_RE = re.compile(r"(?P<host>[a-zA-Z0-9.-]+):(?P<port>\d{2,5})")

# bore 进程在 Kali 容器内的管理约定。PID / log 文件按 local_port 分隔,
# 便于同一容器里开多条隧道,也方便事后 `pkill` / 重启。
PID_FILE = "/tmp/ctf_bore_{port}.pid"
LOG_FILE = "/tmp/ctf_bore_{port}.log"


@dataclass
class BoreTunnelState:
    local_port: int
    server: str
    container: str
    desired: bool = True
    running: bool = False
    remote_host: Optional[str] = None
    remote_port: Optional[int] = None
    restart_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_exit_code: Optional[int] = None
    last_error: Optional[str] = None
    logs: Deque[str] = field(default_factory=lambda: deque(maxlen=200))

    def to_dict(self) -> dict:
        return {
            "local_port": self.local_port,
            "server": self.server,
            "container": self.container,
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
    """
    管理运行在 Kali 容器内的 bore 进程。

    每条隧道在对应容器里起一个 `bore local <port> --to <server>` 后台进程,
    pid 写到 /tmp/ctf_bore_<port>.pid,stdout/stderr 写到 /tmp/ctf_bore_<port>.log。
    后端用单独的监控线程定期 tail 日志、检查 pid 存活,保持 desired 语义。
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tunnels: Dict[int, BoreTunnelState] = {}
        self._monitors: Dict[int, threading.Thread] = {}

    # ------------------------------------------------------------------ 对外 API

    def start_tunnel(self, local_port: int, server: Optional[str] = None) -> BoreTunnelState:
        target_server = server or settings.bore_server
        container = runtime_state.get_active_container()
        if not container:
            raise RuntimeError("no active container set")

        with self._lock:
            state = self._tunnels.get(local_port)
            if state and state.desired and state.running and state.container == container:
                return state

            if state is None:
                state = BoreTunnelState(
                    local_port=local_port, server=target_server, container=container
                )
                self._tunnels[local_port] = state
            else:
                state.server = target_server
                state.container = container
                state.desired = True
                state.last_error = None

            self._spawn_locked(state)
            self._ensure_monitor_locked(local_port)
            return state

    def stop_tunnel(self, local_port: int) -> BoreTunnelState:
        with self._lock:
            state = self._tunnels.get(local_port)
            if state is None:
                raise ValueError(f"no bore tunnel found for local port {local_port}")
            state.desired = False
            container = state.container

        self._kill_in_container(container, local_port)

        with self._lock:
            state.running = False
            state.logs.append("stopped by request")
            return state

    def list_tunnels(self) -> list[dict]:
        with self._lock:
            return [state.to_dict() for _, state in sorted(self._tunnels.items())]

    # ---------------------------------------------------------------- 进程管理

    def _spawn_locked(self, state: BoreTunnelState) -> None:
        pid_path = PID_FILE.format(port=state.local_port)
        log_path = LOG_FILE.format(port=state.local_port)
        # 清掉老 log,新进程从头开始写,方便监控线程定位 remote_port
        bore_cmd = (
            f"{shlex.quote(settings.bore_binary)} local "
            f"{state.local_port} --to {shlex.quote(state.server)}"
        )
        shell = (
            f": > {shlex.quote(log_path)}; "
            f"rm -f {shlex.quote(pid_path)}; "
            f"setsid nohup {bore_cmd} >{shlex.quote(log_path)} 2>&1 & "
            f"echo $! > {shlex.quote(pid_path)}"
        )

        try:
            container_obj = self._get_container(state.container)
            result = container_obj.exec_run(
                ["/bin/bash", "-lc", shell], detach=False, demux=False
            )
            if result.exit_code not in (0, None):
                output = result.output.decode("utf-8", errors="replace") if isinstance(result.output, bytes) else str(result.output)
                raise RuntimeError(f"exec failed ({result.exit_code}): {output.strip()}")
        except Exception as exc:
            state.running = False
            state.last_error = f"failed to spawn bore in {state.container}: {exc}"
            raise RuntimeError(state.last_error) from exc

        state.running = True
        state.started_at = datetime.utcnow()
        state.remote_host = None
        state.remote_port = None
        state.last_exit_code = None
        state.logs.append(
            f"spawned: {bore_cmd} in container={state.container}"
        )

    def _kill_in_container(self, container_name: str, local_port: int) -> None:
        pid_path = PID_FILE.format(port=local_port)
        shell = (
            f"if [ -f {shlex.quote(pid_path)} ]; then "
            f"  pid=$(cat {shlex.quote(pid_path)}); "
            f"  kill -TERM $pid 2>/dev/null; "
            f"  for i in 1 2 3; do kill -0 $pid 2>/dev/null || break; sleep 1; done; "
            f"  kill -KILL $pid 2>/dev/null; "
            f"  rm -f {shlex.quote(pid_path)}; "
            f"fi; "
            # 兜底:按命令行模式清理(例如 pid 文件丢了)
            f"pkill -f {shlex.quote(f'bore local {local_port} ')} 2>/dev/null || true"
        )
        try:
            container_obj = self._get_container(container_name)
            container_obj.exec_run(["/bin/bash", "-lc", shell], detach=False, demux=False)
        except Exception:  # 容器已经没了之类的,stop 不应报错阻塞 desired 语义
            pass

    def _get_container(self, name: str):
        # 避免 import 环;运行时从 DockerService 取 client
        from app.core.docker import get_docker_service

        return get_docker_service().client.containers.get(name)

    # ---------------------------------------------------------------- 监控循环

    def _ensure_monitor_locked(self, local_port: int) -> None:
        existing = self._monitors.get(local_port)
        if existing is not None and existing.is_alive():
            return
        thread = threading.Thread(target=self._monitor, args=(local_port,), daemon=True)
        self._monitors[local_port] = thread
        thread.start()

    def _monitor(self, local_port: int) -> None:
        log_path = LOG_FILE.format(port=local_port)
        pid_path = PID_FILE.format(port=local_port)
        last_log_size = 0

        while True:
            with self._lock:
                state = self._tunnels.get(local_port)
                if state is None:
                    return
                container = state.container
                desired = state.desired

            # 抓日志增量 + 探活
            alive, exit_code, new_logs, new_size = self._poll_tunnel(
                container, log_path, pid_path, last_log_size
            )
            last_log_size = new_size

            with self._lock:
                state = self._tunnels.get(local_port)
                if state is None:
                    return
                for line in new_logs:
                    state.logs.append(line)
                    self._parse_remote_addr_locked(state, line)

                if alive:
                    state.running = True
                else:
                    state.running = False
                    if exit_code is not None:
                        state.last_exit_code = exit_code
                    if not state.desired:
                        return
                    state.restart_count += 1
                    state.logs.append(f"bore exited (code={exit_code}), restarting")

            if not desired:
                return

            if not alive:
                time.sleep(max(1, settings.bore_restart_backoff_seconds))
                with self._lock:
                    state = self._tunnels.get(local_port)
                    if state is None or not state.desired:
                        return
                    try:
                        self._spawn_locked(state)
                        last_log_size = 0  # log 被清掉了
                    except RuntimeError as exc:
                        state.last_error = str(exc)
                        time.sleep(max(5, settings.bore_restart_backoff_seconds * 2))
                continue

            time.sleep(2)

    def _poll_tunnel(
        self,
        container_name: str,
        log_path: str,
        pid_path: str,
        last_log_size: int,
    ) -> tuple[bool, Optional[int], list[str], int]:
        """
        返回 (alive, last_exit_code, new_log_lines, current_log_size)。
        通过一次 exec 把 pid 活性 + log 大小 + 增量一起取出。
        """
        probe = (
            f"if [ -f {shlex.quote(pid_path)} ] && kill -0 $(cat {shlex.quote(pid_path)}) 2>/dev/null; "
            f"then echo ALIVE; else echo DEAD; fi; "
            f"wc -c < {shlex.quote(log_path)} 2>/dev/null || echo 0; "
            f"echo '---BEGIN-LOG---'; "
            f"tail -c +{last_log_size + 1} {shlex.quote(log_path)} 2>/dev/null || true"
        )
        try:
            container_obj = self._get_container(container_name)
            result = container_obj.exec_run(
                ["/bin/bash", "-lc", probe], detach=False, demux=False
            )
        except Exception:
            return False, None, [f"probe failed: container {container_name} unavailable"], last_log_size

        output = result.output.decode("utf-8", errors="replace") if isinstance(result.output, bytes) else str(result.output)
        parts = output.split("---BEGIN-LOG---", 1)
        header = parts[0]
        tail = parts[1] if len(parts) > 1 else ""

        header_lines = header.strip().splitlines()
        alive = bool(header_lines) and header_lines[0].strip() == "ALIVE"
        try:
            current_size = int(header_lines[1].strip()) if len(header_lines) > 1 else last_log_size
        except ValueError:
            current_size = last_log_size

        new_lines: list[str] = []
        for raw in tail.splitlines():
            clean = _strip_ansi(raw).strip()
            if clean:
                new_lines.append(clean)

        return alive, None, new_lines, max(current_size, last_log_size)

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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


_bore_manager: Optional[BoreManager] = None


def get_bore_manager() -> BoreManager:
    global _bore_manager
    if _bore_manager is None:
        _bore_manager = BoreManager()
    return _bore_manager

from __future__ import annotations
from queue import Empty, Queue
import threading
import time

from core.enumerator import probe


def _worker(task_queue: Queue[str], result_queue: Queue[dict], host: str,
           port: int, method: str, timeout: float, use_tls: bool, delay: float, username: str | None, password: str | None) -> None:
    """
    Process each path in task_queue and push the result into result_queue.

    Args:
        task_queue: Queue contains the paths that need to be probed
        result_queue: Queue contains the result dictionary from each probe
        host: IP/domain server
        port: RTSP/RTSPS port
        method: RTSP method
        timeout: Maximum waiting time for responses
        use_tls: True if using RTSP over TLS
        delay: Interval between probes to reduce speed
        username: Username for authentication
        password: Password for authentication
    """
    while True:
        try:
            path = task_queue.get(timeout=1.0)
        except Empty:
            return

        try:
            try:
                status, reason, recv_ms, error = probe.probe(
                    host=host, port=port, path=path,
                    timeout=timeout, method=method, use_tls=use_tls,
                    username=username, password=password,
                )
            except Exception as e:
                status, reason, recv_ms, error = None, "", 0.0, f"worker: {e}"

            result_queue.put({
                "method":  method,
                "path":    path,
                "status":  status,
                "reason":  reason,
                "recv_ms": recv_ms,
                "error":   error,
            })

            if delay > 0:
                time.sleep(delay)
        finally:
            task_queue.task_done()


def _build_task_queue(paths: list[str]) -> Queue[str]:
    """
    Create task_queue and load all URL paths.

    Args:
        paths: List of normalized paths

    Returns:
        Queue contains paths ready for worker
    """
    q: Queue[str] = Queue()
    for p in paths:
        q.put(p)
    return q


def _spawn_workers(task_queue: Queue[str], result_queue: Queue[dict], host: str,
                  port: int, method: str, timeout: float, use_tls: bool,
                  delay: float, n_threads: int,
                  username: str | None = None, password: str | None = None) -> list[threading.Thread]:
    """
    Spawn N worker thread.

    Args:
        task_queue   : Queue contains normalized paths
        result_queue : Queue contains results
        host         : IP/domain server
        port         : RTSP/RTSPS port
        method       : RTSP method
        timeout      : Maximum waiting time for responses
        use_tls      : True if using RTSP over TLS
        delay        : Interval between probes to reduce speed
        n_threads    : Maximum number of threads
        username: Username for authentication
        password: Password for authentication

    Returns:
        List of threads which have been started
    """
    threads = []
    for _ in range(n_threads):
        t = threading.Thread(
            target=_worker,
            args=(task_queue, result_queue, host, port,
                  method, timeout, use_tls, delay, username, password),
            daemon=True,
        )
        t.start()
        threads.append(t)
    return threads


def join_workers(threads: list[threading.Thread]) -> bool:
    """
    Wait for all workers stopped.

    Args:
        threads: List of threads which have been started (get from spawn_workers())

    Returns:
        True if threads complete norally
        False if the main process is interrupted by Ctrl+C
    """
    try:
        for t in threads:
            t.join()
        return True
    except KeyboardInterrupt:
        return False


def start_probe(paths: list[str], host: str, port: int, method: str,
                timeout: float, use_tls: bool, delay: float, n_threads: int,
                username: str | None = None, password: str | None = None) -> tuple[Queue[dict], list[threading.Thread]]:
    """
    Start the RTSP probe process in parallel.
    Spawns worker threads and returns immediately, allowing the caller
    to consume results from the result queue in real time.

    Args:
        paths: List of normalized RTSP paths to probe.
        host: Target hostname or IP address.
        port: Target RTSP/RTSPS port.
        method: RTSP method to use (e.g., "DESCRIBE", "OPTIONS").
        timeout: Maximum wait time per probe, in seconds.
        use_tls: True to use RTSP over TLS (rtsps://).
        delay: Delay between probes, in seconds (0 for no delay).
        n_threads: Maximum number of worker threads to spawn.
        username: Username for authentication
        password: Password for authentication
    Returns:
        A tuple of:
        - result_queue: Queue that workers push result dicts into.
        - threads: List of started Thread objects (for joining later).
    """
    task_queue: Queue[str] = _build_task_queue(paths)
    result_queue: Queue[dict] = Queue()

    n_threads = max(1, n_threads)
    actual_threads = min(n_threads, len(paths)) if paths else 1

    threads = _spawn_workers(task_queue, result_queue, host, port, method, timeout,
                             use_tls, delay, actual_threads, username, password)

    return result_queue, threads

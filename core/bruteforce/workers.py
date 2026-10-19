from __future__ import annotations
import threading
import time
from queue import Empty, Queue

from core.bruteforce import engine


__all__ = [
    "start_brute",
    "join_workers",
]


def _worker(task_queue: Queue[tuple[str, str]], result_queue: Queue[dict],
            url: str, method: str, timeout: float, use_tls: bool,
            delay: float, stop_event: threading.Event, stop_on_succeed: bool) -> None:
    """
    Consume (username, password) pairs from task_queue, try each against
    the RTSP server, and push a result dict into result_queue.

    Args:
        task_queue: Queue containing (username, password) tuples.
        result_queue: Queue receiving result dictionaries.
        url: Full RTSP/RTSPS URL (from create_url).
        method: RTSP method used for authentication (e.g. DESCRIBE).
        timeout: Maximum wait time per credential, in seconds.
        use_tls: True to use RTSP over TLS (rtsps://).
        delay: Delay between attempts, in seconds (0 for no delay).
        stop_event: Event that, once set, tells workers to stop.
        stop_on_succeed: If True, stop all workers as soon as a credential
            succeeds.
    """
    while not stop_event.is_set():
        try:
            credential: tuple[str, str] = task_queue.get(timeout=1.0)
        except Empty:
            return

        username, password = credential
        try:
            try:
                ok, message = engine.try_credentials(
                    url=url,
                    method=method,
                    username=username,
                    password=password,
                    timeout=timeout,
                    use_tls=use_tls,
                )
            except Exception as e:
                ok, message = False, f"worker: {e}"

            result_queue.put({
                "username": username,
                "password": password,
                "ok": ok,
                "message": message,
            })

            if ok and stop_on_succeed:
                stop_event.set()
                return

            if delay > 0:
                time.sleep(delay)
        finally:
            task_queue.task_done()


def _build_task_queue(credentials: list[tuple[str, str]]) -> Queue[tuple[str, str]]:
    """
    Create a task queue preloaded with all credential pairs.

    Args:
        credentials: List of (username, password) tuples.

    Returns:
        A Queue ready to be consumed by workers.
    """
    q: Queue[tuple[str, str]] = Queue()
    for c in credentials:
        q.put(c)
    return q


def _spawn_workers(task_queue: Queue[tuple[str, str]], result_queue: Queue[dict],
                   url: str, method: str, timeout: float, use_tls: bool,
                   delay: float, n_threads: int, stop_event: threading.Event,
                   stop_on_succeed: bool) -> list[threading.Thread]:
    """
    Spawn and start N worker threads.

    Args:
        task_queue: Queue containing (username, password) tuples.
        result_queue: Queue receiving result dictionaries.
        url: Full RTSP/RTSPS URL.
        method: RTSP method used for authentication.
        timeout: Maximum wait time per credential, in seconds.
        use_tls: True to use RTSP over TLS.
        delay: Delay between attempts, in seconds.
        n_threads: Number of worker threads to spawn.
        stop_event: Shared event to signal workers to stop.
        stop_on_succeed: If True, stop all workers on first success.

    Returns:
        List of started Thread objects.
    """
    threads: list[threading.Thread] = []
    for _ in range(n_threads):
        t = threading.Thread(
            target=_worker,
            args=(task_queue, result_queue, url, method, timeout, use_tls,
                  delay, stop_event, stop_on_succeed),
            daemon=True,
        )
        t.start()
        threads.append(t)
    return threads


def join_workers(threads: list[threading.Thread]) -> bool:
    """
    Wait for all workers to finish.

    Args:
        threads: List of started Thread objects.

    Returns:
        True if all workers completed normally, False if interrupted by Ctrl+C.
    """
    try:
        for t in threads:
            t.join()
        return True
    except KeyboardInterrupt:
        return False


def start_brute(url: str, credentials: list[tuple[str, str]], method: str = "DESCRIBE",
                timeout: float = 5.0, use_tls: bool = False, delay: float = 0.0,
                n_threads: int = 4, stop_on_succeed: bool = False
                ) -> tuple[Queue[dict], list[threading.Thread], threading.Event]:
    """
    Start the RTSP brute-force process in parallel.

    Spawns worker threads and returns immediately, allowing the caller
    to consume results from the result queue in real time.

    Args:
        url: Full RTSP/RTSPS URL (from create_url).
        credentials: List of (username, password) tuples to try.
        method: RTSP method used for authentication (default: DESCRIBE).
        timeout: Maximum wait time per credential, in seconds.
        use_tls: True to use RTSP over TLS (rtsps://).
        delay: Delay between attempts, in seconds (0 for no delay).
        n_threads: Maximum number of worker threads to spawn.
        stop_on_succeed: If True, stop all workers on first successful
            credential.

    Returns:
        A tuple of:
        - result_queue: Queue that workers push result dicts into.
        - threads: List of started Thread objects (for joining later).
        - stop_event: Event that can be set to signal workers to stop.
    """
    task_queue: Queue[tuple[str, str]] = _build_task_queue(credentials)
    result_queue: Queue[dict] = Queue()
    stop_event = threading.Event()

    n_threads = max(1, n_threads)
    actual_threads = min(n_threads, len(credentials)) if credentials else 1

    threads = _spawn_workers(task_queue, result_queue, url, method, timeout,
                             use_tls, delay, actual_threads, stop_event,
                             stop_on_succeed)

    return result_queue, threads, stop_event

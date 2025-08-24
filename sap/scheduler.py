from __future__ import annotations
import threading
import time
from typing import Any, Callable, List, Optional


class IntervalCacheRunner:
    def __init__(
        self,
        fetch_fn: Callable[[], List[dict]],
        interval_seconds: float,
        run_immediately: bool = True,
    ) -> None:
        self._fetch_fn = fetch_fn
        self._interval_seconds = max(0.0, float(interval_seconds))
        self._run_immediately = run_immediately

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._last_started_at: Optional[float] = None
        self._last_completed_at: Optional[float] = None
        self._last_error: Optional[str] = None
        self._cache: List[dict] = []

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="sap-interval-runner", daemon=True)
        self._thread.start()

    def stop(self, timeout: Optional[float] = 5.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def get_cached(self) -> List[dict]:
        with self._lock:
            return list(self._cache)

    def get_status(self) -> dict:
        with self._lock:
            return {
                "last_started_at": self._last_started_at,
                "last_completed_at": self._last_completed_at,
                "last_error": self._last_error,
                "interval_seconds": self._interval_seconds,
                "is_running": self._thread.is_alive() if self._thread else False,
            }

    def _run_once(self) -> None:
        try:
            self._last_started_at = time.time()
            result = self._fetch_fn()
            if not isinstance(result, list):
                raise TypeError("fetch function must return a list of SA JSON objects (dicts)")
            # Cheap validation of element type
            if any(not isinstance(item, dict) for item in result):
                raise TypeError("each item returned by fetch must be a dict")
            with self._lock:
                self._cache = result
                self._last_completed_at = time.time()
                self._last_error = None
        except Exception as exc:
            with self._lock:
                self._last_error = f"{type(exc).__name__}: {exc}"
                self._last_completed_at = time.time()

    def _run_loop(self) -> None:
        if self._run_immediately:
            self._run_once()
        # Loop forever until stopped
        while not self._stop_event.is_set():
            # Sleep up to interval, but wake early if stop requested
            waited = 0.0
            while waited < self._interval_seconds and not self._stop_event.is_set():
                sleep_chunk = min(0.5, self._interval_seconds - waited)
                time.sleep(sleep_chunk)
                waited += sleep_chunk
            if self._stop_event.is_set():
                break
            self._run_once()
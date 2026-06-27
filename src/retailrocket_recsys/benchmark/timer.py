from __future__ import annotations

import time
from dataclasses import dataclass

import psutil


@dataclass
class Timer:
    step: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    rss_memory_mb: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # noqa: ANN001
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.rss_memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)

    def as_dict(self) -> dict[str, float | str]:
        return {
            "step": self.step,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "rss_memory_mb": self.rss_memory_mb,
        }

from __future__ import annotations

import time
from typing import Callable

TimeFunc = Callable[[], float]


class LoopTimer:
    def __init__(self, delay: float, *, timefunc: TimeFunc = time.perf_counter):
        self._delay: float = delay
        self._time: TimeFunc = timefunc
        self._start: float = 0
        self._loops: int = 0

    @property
    def delay(self) -> float:
        return self._delay

    @property
    def loops(self) -> int:
        return self._loops

    @property
    def start_time(self) -> float:
        return self._start

    @property
    def remaining_time(self) -> float:
        next_time = self._start + self._delay * self._loops
        return self._delay + (next_time - self._time())

    def start(self) -> None:
        self._loops = 0
        self._start = self._time()

    def mark(self) -> None:
        self._loops += 1

    def sleep(self) -> None:
        time.sleep(max(0, self.remaining_time))

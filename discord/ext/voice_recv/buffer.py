# -*- coding: utf-8 -*-

from __future__ import annotations

import heapq
import bisect
import threading

from collections import deque

from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Optional, List, Deque, Literal
    from .rtp import RTPPacket

__all__ = [
    'HeapJitterBuffer',
]


# class NoPacket:
#     __slots__ = ('sequence',)
#
#     def __init__(self, seq: int):
#         self.sequence = seq
#         # TODO: timestamp?
#
#     def __repr__(self):
#         return f'<{type(self).__name__} seq={self.sequence}>'
#
#     def __bool__(self) -> Literal[False]:
#         return False
#
#     def __lt__(self, other):
#         return self.sequence < other.sequence
#
#     def __eq__(self, other):
#         return self.sequence == other.sequence


# if TYPE_CHECKING:
#     SomePacket = RTPPacket | NoPacket


# class OldSimpleJitterBuffer:
#     """Push item in, returns as many contiguous items as possible"""
#
#     def __init__(self, maxsize=10, *, prefill=3):
#         if maxsize < 1:
#             raise ValueError('maxsize must be greater than 0')
#
#         self.maxsize = maxsize
#         self.prefill = prefill
#         self._prefill = prefill # original prefill
#         self._last_seq: int = 0
#         self._buffer: list[RTPPacket] = []
#
#     def __len__(self):
#         return len(self._buffer)
#
#     def push(self, item: RTPPacket) -> list[RTPPacket | None]:
#         if item.sequence <= self._last_seq and self._last_seq:
#             return []
#
#         bisect.insort(self._buffer, item)
#
#         if self.prefill > 0:
#             self.prefill -= 1
#             return []
#
#         return self._get_ready_batch()
#
#     def _get_ready_batch(self) -> list[RTPPacket | None]:
#         if not self._buffer or self.prefill > 0:
#             return []
#
#         if not self._last_seq:
#             self._last_seq = self._buffer[0].sequence - 1
#
#         # check to see if the next packet is the next one
#         if self._last_seq + 1 == self._buffer[0].sequence:
#
#             # Check for how many contiguous packets we have
#             n = ok = 0
#             for n in range(len(self._buffer)): # TODO: enumerate
#                 if self._last_seq + n + 1 != self._buffer[n].sequence:
#                     break
#                 ok = n + 1
#
#             # slice out the next section of the buffer
#             segment = self._buffer[:ok]
#             self._buffer = self._buffer[ok:]
#             if segment:
#                 self._last_seq = segment[-1].sequence
#
#             return segment # type: ignore
#
#         # size check and add skips as None
#         if len(self._buffer) > self.maxsize:
#             buf: list[RTPPacket | None] = [
#                 None for _ in range(self._buffer[0].sequence-self._last_seq-1)
#             ]
#             self._last_seq = self._buffer[0].sequence - 1
#             buf.extend(self._get_ready_batch())
#             return buf
#
#         return []
#
#     def flush(self, reset: bool=False) -> list[RTPPacket | None]:
#         if reset:
#             self.prefill = self._prefill
#
#         if not self._buffer:
#             return []
#
#         seq = self._buffer[0].sequence
#         remaining: list[RTPPacket | None] = []
#
#         if self._last_seq + 1 != seq:
#             assert self._last_seq + 1 < seq
#             jump = seq - self._last_seq + 1
#             remaining.extend(None for _ in range(jump))
#
#         for packet in self._buffer:
#             gap = packet.sequence - seq
#             remaining.extend(None for _ in range(gap))
#             remaining.append(packet)
#             seq = packet.sequence + 1
#
#         return remaining
#
#
# class SimpleJitterBuffer:
#     """Push item in, pop items out"""
#
#     def __init__(self, maxsize: int=10, *, prefsize: int=1, prefill: int=1):
#         if maxsize < 1:
#             raise ValueError(f'maxsize ({maxsize}) must be greater than 0')
#
#         if not 0 <= prefsize <= maxsize:
#             raise ValueError(f'prefsize must be between 0 and maxsize ({maxsize})')
#
#         self.maxsize = maxsize
#         self.prefsize = prefsize
#         self.prefill = prefill
#         self._prefill = prefill # original prefill
#         self._last_seq: int = 0 # the sequence of the last packet popped from the buffer
#         self._has_item = threading.Event()
#         self._buffer: Deque[SomePacket] = deque(maxlen=maxsize)
#         # I sure hope I dont need to add a lock to this
#
#     def __len__(self):
#         return len(self._buffer)
#
#     def _get_ready_packet(self) -> SomePacket | None:
#         return self._buffer[0] if len(self._buffer) > self.prefsize else None
#
#     def _pop_if_ready(self) -> SomePacket | None:
#         return self._buffer.popleft() if len(self._buffer) > self.prefsize else None
#
#     def _update_has_item(self):
#         prefilled = self.prefill == 0
#         packet_ready = len(self._buffer) > self.prefsize
#
#         if not prefilled or not packet_ready:
#             self._has_item.clear()
#             return
#
#         sequential = self._last_seq + 1 == self._buffer[0].sequence
#         positive_seq = self._last_seq > 0
#
#         # We have the next packet ready OR we havent sent a packet out yet
#         if (sequential and positive_seq) or not positive_seq:
#             self._has_item.set()
#         else:
#             self._has_item.clear()
#
#     def _is_next_packet(self, packet: SomePacket) -> bool:
#         # Haven't sent out a packet yet
#         if self._last_seq == 0:
#             # If we even have any packets
#             if self._buffer:
#                 # If this packet is the first packet we're good
#                 return packet.sequence == self._buffer[0].sequence
#             else:
#                 # This would be the only packet (unusual situation)
#                 return True
#
#         return self._last_seq + 1 == packet.sequence
#
#     def _cleanup(self):
#         while True:
#             if self._buffer and self._buffer[0].sequence <= self._last_seq:
#                 self._buffer.popleft()
#             else:
#                 break
#
#     def gap(self) -> int:
#         """
#         Returns the number of missing packets between the last packet to be
#         popped and the currently held next packet.  Returns 0 otherwise.
#         """
#
#         if self._last_seq > 0 and self._buffer:
#             return self._buffer[0].sequence - self._last_seq + 1
#
#         return 0
#
#     def peek(self, *, all: bool=False) -> SomePacket | None:
#         """
#         Returns the next packet in the buffer only if it is sequential.
#         When `all` is set to False, it returns the next packet, if any.
#         """
#
#         if not self._buffer:
#             return None
#
#         if all:
#             return self._buffer[0]
#         else:
#             maybe_next = self._get_ready_packet()
#
#             if maybe_next is None:
#                 return None
#
#             elif self._is_next_packet(maybe_next):
#                 return maybe_next
#
#             else:
#                 return None
#
#     def push(self, packet: RTPPacket) -> bool:
#         """TODO"""
#
#         # Ignore the packet if its too old
#         if packet.sequence <= self._last_seq and self._last_seq:
#             return False
#
#         bisect.insort(self._buffer, packet)
#
#         if self.prefill > 0:
#             self.prefill -= 1
#
#         self._cleanup() # we need to do this in case a push cycles the deque
#         self._update_has_item()
#
#         return True
#
#     @overload
#     def pop(self, *, timeout: int=1) -> SomePacket:
#         ...
#
#     @overload
#     def pop(self, *, timeout: Literal[0]) -> SomePacket | None:
#         ...
#
#     def pop(self, *, timeout=1):
#         """TODO"""
#
#         if timeout > 0:
#             ok = self._has_item.wait(timeout)
#             if not ok:
#                 raise TimeoutError
#
#         if self.prefill > 0:
#             return None
#
#         if not self._has_item.is_set():
#             return
#
#         packet = self._pop_if_ready()
#
#         if packet is not None:
#             self._last_seq = packet.sequence
#
#         self._update_has_item()
#         return packet
#
#     def skip(self):
#         """TODO"""
#
#         self._last_seq += 1
#         self._cleanup()
#         self._update_has_item()
#
#     def flush(self, *, reset: bool=False) -> list[SomePacket]:
#         """TODO"""
#
#         packets = list(self._buffer)
#         self._buffer.clear()
#
#         if packets:
#             self._last_seq = packets[-1].sequence
#
#         if reset:
#             self.prefill = self._prefill
#             self._last_seq = 0
#             self._has_item.clear()
#
#         return packets


class HeapJitterBuffer:
    """Push item in, pop items out"""

    def __init__(self, maxsize: int=10, *, prefsize: int=1, prefill: int=1):
        if maxsize < 1:
            raise ValueError(f'maxsize ({maxsize}) must be greater than 0')

        if not 0 <= prefsize <= maxsize:
            raise ValueError(f'prefsize must be between 0 and maxsize ({maxsize})')

        self.maxsize = maxsize
        self.prefsize = prefsize
        self.prefill = self._prefill = prefill

        self._last_rx: int = 0
        self._last_tx: int = 0

        self._has_item = threading.Event()
        # I sure hope I dont need to add a lock to this
        self._buffer: list[tuple[int, RTPPacket]] = []

    def __len__(self):
        return len(self._buffer)

    def _push(self, packet: RTPPacket):
        heapq.heappush(self._buffer, (packet.sequence, packet))

    def _pop(self) -> RTPPacket:
        return heapq.heappop(self._buffer)[1]

    def _n(self, n: int) -> RTPPacket | None:
        return heapq.nsmallest(n, self._buffer)[-1][1]

    def _get_packet_if_ready(self) -> RTPPacket | None:
        return self._buffer[0][1] if len(self._buffer) > self.prefsize else None

    def _pop_if_ready(self) -> RTPPacket | None:
        return self._pop() if len(self._buffer) > self.prefsize else None

    def _update_has_item(self):
        prefilled = self._prefill == 0
        packet_ready = len(self._buffer) > self.prefsize

        if not prefilled or not packet_ready:
            self._has_item.clear()
            return

        sequential = self._last_tx + 1 == self._buffer[0][0]
        positive_seq = self._last_tx > 0

        # We have the next packet ready OR we havent sent a packet out yet
        if (sequential and positive_seq) or not positive_seq:
            self._has_item.set()
        else:
            self._has_item.clear()

    def _cleanup(self):
        while self._buffer and self._buffer[0][0] <= self._last_tx:
            heapq.heappop(self._buffer)

    def push(self, packet: RTPPacket) -> bool:
        """TODO"""

        # Ignore the packet if its too old
        if packet.sequence <= self._last_rx and self._last_rx > 0:
            return False

        self._push(packet)

        if self._prefill > 0:
            self._prefill -= 1

        self._last_rx = packet.sequence

        # self._cleanup() # we need to do this in case a push cycles the deque
        self._update_has_item()

        return True

    @overload
    def pop(self, *, timeout: float=1.0) -> RTPPacket | None:
        ...

    @overload
    def pop(self, *, timeout: Literal[0]) -> RTPPacket | None:
        ...

    def pop(self, *, timeout=1.0):
        """TODO
        If timeout is a positive number, wait as long as timeout for a packet
        to be ready and return that packet, otherwise return None.
        """

        ok = self._has_item.wait(timeout)
        if not ok:
            return None

        if self._prefill > 0:
            return None

        # This function should actually be redundant but i'll leave it for now
        packet = self._pop_if_ready()

        if packet is not None:
            self._last_tx = packet.sequence

        self._update_has_item()
        return packet


    def peek(self, *, all: bool=False) -> RTPPacket | None:
        """
        Returns the next packet in the buffer only if it is ready, meaning it can
        be popped. When `all` is set to False, it returns the next packet, if any.
        """

        if not self._buffer:
            return None

        if all:
            return self._buffer[0][1]
        else:
            return self._get_packet_if_ready()

    def peek_next(self) -> RTPPacket | None:
        """
        Returns the next packet in the buffer only if it is sequential.
        """

        packet = self.peek(all=True)

        if packet and packet.sequence == self._last_tx + 1:
            return packet

    def gap(self) -> int:
        """
        Returns the number of missing packets between the last packet to be
        popped and the currently held next packet.  Returns 0 otherwise.
        """

        if self._buffer and self._last_tx > 0:
            return self._buffer[0][0] - self._last_tx + 1

        return 0

    def flush(self, *, reset: bool=False) -> list[RTPPacket]:
        """
        Return all remaining packets and optionally reset internal counters.
        """

        packets = [p for (s, p) in sorted(self._buffer)]
        self._buffer.clear()

        if packets:
            self._last_seq = packets[-1].sequence

        self._prefill = self.prefill
        self._has_item.clear()

        if reset:
            self._last_tx = self._last_rx = 0

        return packets

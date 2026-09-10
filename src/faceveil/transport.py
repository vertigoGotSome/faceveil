"""One shared frame slot avoids queuing and pickling full-resolution frames."""

import numpy as np

MAX_BYTES = 1280 * 720 * 3


class FrameMailbox:
    def __init__(self, context):
        self.data = context.RawArray("B", MAX_BYTES)
        self.header = context.RawArray("q", 4)
        self.lock = context.Lock()

    def publish(self, frame, generation):
        if frame.dtype != np.uint8 or frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError("Expected uint8 BGR frame")
        if frame.size > MAX_BYTES:
            raise ValueError("Frame exceeds shared slot")
        with self.lock:
            np.frombuffer(self.data, dtype=np.uint8)[: frame.size] = frame.reshape(-1)
            self.header[0] += 1
            self.header[1:] = (generation, frame.shape[0], frame.shape[1])
            return self.header[0]

    def read(self, sequence, generation):
        if not self.lock.acquire(False):
            return None
        try:
            current, actual_generation, height, width = self.header
            if current != sequence or actual_generation != generation or not height:
                return None
            return (
                np.frombuffer(self.data, dtype=np.uint8)[: height * width * 3]
                .reshape(height, width, 3)
                .copy()
            )
        finally:
            self.lock.release()

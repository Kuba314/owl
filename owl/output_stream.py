from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping
import logging
import wave

import numpy as np
import pyaudio

from owl.types import Signal


logger = logging.getLogger("output_stream")


@dataclass(kw_only=True)
class AudioOutputStream(ABC):
    sample_rate: int = 48000
    chunk_size: int = 1024

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def write(self, signal: Signal) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


@dataclass
class LiveAudioOutputStream(AudioOutputStream):
    _stream: pyaudio.Stream | None = field(default=None)
    _queue: list[float] = field(default_factory=list)

    def open(self) -> None:
        if self._stream is not None:
            raise Exception("output stream already open")

        logger.info("opening PyAudio stream")

        pa = pyaudio.PyAudio()
        self._stream = pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._callback,
        )

    def write(self, signal: Signal) -> None:
        self._queue.extend(signal)

    def close(self) -> None:
        if self._stream is None:
            raise Exception("output stream is not open")

        logger.info("closing PyAudio stream")
        self._stream.close()
        self._stream = None

    def _callback(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        if len(self._queue) < frame_count:
            logger.warning(f"underflow, need {frame_count} samples but have only {len(self._queue)}")
            return np.zeros((frame_count,), dtype=np.float32).tobytes(), pyaudio.paContinue

        data = self._queue[:frame_count]
        self._queue = self._queue[frame_count:]
        return np.array(data, dtype=np.float32).tobytes(), pyaudio.paContinue


@dataclass
class FileAudioOutputStream(AudioOutputStream):
    filename: str
    _stream: wave.Wave_write | None = field(default=None)

    def open(self) -> None:
        if self._stream is not None:
            raise Exception("output stream already open")

        logger.info("opening wav stream")

        stream = wave.open(self.filename, mode="wb")
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(self.sample_rate)
        self._stream = stream

    def write(self, signal: Signal) -> None:
        if self._stream is None:
            raise Exception("output stream is not open")

        data = (signal * 16383).astype(np.int16).tobytes()
        self._stream.writeframes(data)

    def close(self) -> None:
        if self._stream is None:
            raise Exception("output stream is not open")

        logger.info("closing wav stream")
        self._stream.close()

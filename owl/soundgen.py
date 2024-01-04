from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial
from threading import Thread
import itertools
import logging
import time
import wave

from pyaudio import Stream
import numpy as np
import numpy.typing as npt
import pyaudio

from owl.types import Signal


logger = logging.getLogger("soundgen")


@dataclass
class Envelope:
    attack_duration: float
    decay_duration: float
    release_duration: float
    sustain_level: float

    def apply(self, signal: np.ndarray, sample_rate: int) -> np.ndarray:
        attack_duration = int(self.attack_duration * sample_rate)
        decay_duration = int(self.decay_duration * sample_rate)
        release_duration = int(self.release_duration * sample_rate)
        sustain_duration = (
            len(signal) - attack_duration - decay_duration - release_duration
        )

        attack = 1 - np.linspace(-1, 0, attack_duration) ** 2
        decay = (
            np.linspace(-1, 0, decay_duration) ** 2 * (1 - self.sustain_level)
            + self.sustain_level
        )
        sustain = np.full((sustain_duration,), self.sustain_level)
        release = np.linspace(-1, 0, release_duration) ** 2 * self.sustain_level

        env = np.concatenate((attack, decay, sustain, release))
        out = signal * env
        return out


@dataclass
class FreqGen:
    frequency: float
    sample_rate: int
    initial_volume: float = 1.0

    def __post_init__(self) -> None:
        logger.debug(
            f"Initializing FreqGen(hz={self.frequency:.02f}, Fs={self.sample_rate})"
        )

        signal = np.sin(
            np.linspace(
                0, 2 * np.pi, int(self.sample_rate / self.frequency), endpoint=False
            )
        )

        self._freq_gen: Iterator[float] = itertools.cycle(signal)
        self._vol_gen: Iterator[float] = itertools.repeat(self.initial_volume)

    def get_next_samples(self, count: int) -> npt.NDArray[np.float32]:
        freqs = np.fromiter(self._freq_gen, float, count=count)
        vols = np.fromiter(self._vol_gen, float, count=count)
        return freqs * vols  # type: ignore (https://github.com/microsoft/pylance-release/discussions/2660)

    def set_volume(self, volume: float, backoff: float) -> None:
        current_volume = next(self._vol_gen)
        slope_iter = iter(
            np.linspace(current_volume, volume, int(backoff * self.sample_rate))
        )
        self._vol_gen = itertools.chain(slope_iter, itertools.repeat(volume))


@dataclass
class MultiFreqGen:
    freqs: Sequence[float]
    sample_rate: int = 48000

    def __post_init__(self) -> None:
        logger.debug(f"Initializing MultiFreqGen(freqs={self.freqs})")

        self._signal_gens = [
            FreqGen(freq, self.sample_rate, initial_volume=0.0) for freq in self.freqs
        ]

    def set_volumes(self, volumes: Iterable[float], backoff: float) -> None:
        for signal_gen, volume in zip(self._signal_gens, volumes):
            signal_gen.set_volume(volume, backoff=backoff)

    def get_next_samples(self, count) -> Signal:
        signals = [gen.get_next_samples(count) for gen in self._signal_gens]
        return np.sum(signals, axis=0) / len(self._signal_gens)


@dataclass(kw_only=True)
class BaseAudioOutputStream(ABC):
    next_samples_callback: Callable[[int], Signal]
    sample_rate: int = 48000
    chunk_size: int = 1024

    @abstractmethod
    def open(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...


class LiveAudioOutputStream(BaseAudioOutputStream):
    _stream: Stream | None = None

    def open(self) -> None:
        if self._stream is not None:
            raise Exception("Output stream already open")

        logger.info("Opening PyAudio stream")

        pa = pyaudio.PyAudio()
        self._stream = pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._callback,
        )

    def close(self) -> None:
        if self._stream is None:
            raise Exception("Output stream is not open")

        logger.info("Closing PyAudio stream")
        self._stream.close()
        self._stream = None

    def _callback(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        signal = np.array(self.next_samples_callback(frame_count))
        return signal.astype(np.float32).tobytes(), pyaudio.paContinue


@dataclass
class FileAudioOutputStream(BaseAudioOutputStream):
    filename: str
    _thread: Thread | None = field(init=False, default=None)
    _should_stop: bool = field(init=False, default=False)

    def open(self) -> None:
        if self._thread is not None:
            raise Exception("Output stream already open")

        logger.info("Opening wav stream")

        stream = wave.open(self.filename, mode="wb")
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(self.sample_rate)
        self._thread = Thread(
            target=partial(self._sample_request_loop, stream),
        )

        self._should_stop = False
        self._thread.start()

    def close(self) -> None:
        if self._thread is None:
            raise Exception("Output stream is not open")

        logger.info("Closing wav stream")
        self._should_stop = True
        self._thread.join()
        self._thread = None

    def _sample_request_loop(self, stream: wave.Wave_write) -> None:
        logger.debug("Started audio request loop")

        frame_count = self.chunk_size
        fps = self.sample_rate / self.chunk_size

        last_frame = time.time() * 1000
        while not self._should_stop:
            # wait for next frame
            while 1000 * time.time() - last_frame < 1000 / fps:
                time.sleep(0.01)

            signal = self.next_samples_callback(frame_count)
            data = (signal * 16383).astype(np.int16).tobytes()
            stream.writeframes(data)

            last_frame += 1000 / fps

        logger.debug("Stopped audio request loop")
        stream.close()

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
import itertools
import logging

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


@dataclass
class AudioOutputStream:
    next_samples_callback: Callable[[int], Signal]
    sample_rate: int = 48000
    chunk_size: int = 1024

    _stream: Stream | None = field(default=None, init=False)

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

    def __del__(self) -> None:
        if self._stream is not None:
            self.close()

    def _callback(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        signal = np.array(self.next_samples_callback(frame_count))
        return signal.astype(np.float32).tobytes(), pyaudio.paContinue

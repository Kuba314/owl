from dataclasses import dataclass
from collections.abc import Mapping, Iterator, Iterable, Sequence
import itertools

import numpy as np
import pyaudio


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

        attack = np.linspace(0, 1, attack_duration)
        decay = np.linspace(1, self.sustain_level, decay_duration)
        sustain = np.full((sustain_duration,), self.sustain_level)
        release = np.linspace(self.sustain_level, 0, release_duration)

        return signal * np.concatenate((attack, decay, sustain, release))


@dataclass
class FreqGen:
    def __init__(self, frequency: float, sample_rate: int, initial_volume: float = 1.0):
        self.frequency = frequency
        self.sample_rate = sample_rate

        signal = np.sin(
            np.linspace(0, 2 * np.pi, int(sample_rate / frequency), endpoint=False)
        )

        self._freq_gen: Iterator[float] = itertools.cycle(signal)
        self._vol_gen: Iterator[float] = itertools.repeat(initial_volume)

    def get_next_samples(self, count: int) -> np.ndarray:
        freqs = np.fromiter(self._freq_gen, float, count=count)
        vols = np.fromiter(self._vol_gen, float, count=count)
        return freqs * vols

    def set_volume(self, volume: float, backoff: float) -> None:
        current_volume = next(self._vol_gen)
        slope_iter = iter(
            np.linspace(current_volume, volume, int(backoff * self.sample_rate))
        )
        self._vol_gen = itertools.chain(slope_iter, itertools.repeat(volume))


@dataclass
class Soundgen:
    freqs: Sequence[float]
    sample_rate: int = 48000
    chunk_size: int = 1024

    def __post_init__(self) -> None:
        self._signal_gens = [
            FreqGen(freq, self.sample_rate, initial_volume=0.0) for freq in self.freqs
        ]

        pa = pyaudio.PyAudio()
        self._stream = pa.open(
            rate=self.sample_rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._callback,
        )

    def set_volumes(self, volumes: Iterable[float], backoff: float) -> None:
        for signal_gen, volume in zip(self._signal_gens, volumes):
            signal_gen.set_volume(volume, backoff=backoff)

    def stop(self) -> None:
        self._stream.close()

    def __del__(self) -> None:
        self.stop()

    def _callback(
        self,
        in_data: bytes | None,
        frame_count: int,
        time_info: Mapping[str, float],
        status_flags: int,
    ) -> tuple[bytes, int]:
        signals = [gen.get_next_samples(frame_count) for gen in self._signal_gens]
        signal = np.sum(signals, axis=0) / len(self._signal_gens)
        return signal.astype(np.float32).tobytes(), pyaudio.paContinue

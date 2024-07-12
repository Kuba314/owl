from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import Self
import itertools
import logging

import numpy as np
import numpy.typing as npt

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
        return signal * env


@dataclass
class SineGen:
    def __init__(self, initial_frequency: float, sample_rate: int, initial_volume: float = 1.0):
        self.sample_rate = sample_rate

        self._frequency = initial_frequency
        self._volume = initial_volume

        logger.debug(f"initializing SineGen at {initial_frequency:.02f} hz")

        self._phase_gen: Iterator[float] = self._generate_phase_signal(initial_frequency, sample_rate)
        self._vol_gen: Iterator[float] = itertools.repeat(initial_volume)

    def get_next_samples(self, count: int) -> npt.NDArray[np.float32]:
        phases = np.fromiter(self._phase_gen, float, count=count)
        vols = np.fromiter(self._vol_gen, float, count=count)
        return np.sin(phases) * vols  # type: ignore (https://github.com/microsoft/pylance-release/discussions/2660)

    def set_frequency(self, frequency: float, transient_duration: float) -> None:
        current_phase = next(self._phase_gen)

        # inspired by https://stackoverflow.com/a/64971796
        if transient_duration > 0:
            frequency_slope = 2 * np.pi * np.geomspace(self._frequency, frequency, int(transient_duration * self.sample_rate)) / self.sample_rate
            sin_input = frequency_slope.cumsum()
            end_phase = current_phase + sin_input[-1] % (2 * np.pi)
            slope_iter = iter(current_phase + sin_input[:-1])
        else:
            end_phase = current_phase
            slope_iter = iter(())

        self._phase_gen = itertools.chain(
            slope_iter, self._generate_phase_signal(frequency, self.sample_rate, phase=end_phase)
        )
        self._frequency = frequency

    def set_volume(self, volume: float, transient_duration: float) -> None:
        current_volume = next(self._vol_gen)
        slope_iter = iter(
            np.linspace(current_volume, volume, int(transient_duration * self.sample_rate))
        )
        self._vol_gen = itertools.chain(slope_iter, itertools.repeat(volume))

    @classmethod
    def _generate_phase_signal(cls, frequency: float, sample_rate: int, phase: float = 0.0) -> Iterator[float]:
        space = np.linspace(0, 2 * np.pi, int(sample_rate / frequency), endpoint=False)
        return itertools.cycle(phase + space)


@dataclass
class MultiSineGen:
    freqs: Sequence[float]
    sample_rate: int = 48000

    def __post_init__(self) -> None:
        self._signal_gens = [
            SineGen(freq, self.sample_rate, initial_volume=0.0) for freq in self.freqs
        ]

    def set_frequencies(self, frequencies: Iterable[float], transient_duration: float) -> None:
        for signal_gen, frequency in zip(self._signal_gens, frequencies):
            signal_gen.set_frequency(frequency, transient_duration=transient_duration)

    def set_volumes(self, volumes: Iterable[float], transient_duration: float) -> None:
        for signal_gen, volume in zip(self._signal_gens, volumes):
            signal_gen.set_volume(volume, transient_duration=transient_duration)

    def get_next_samples(self, count) -> Signal:
        signals = [gen.get_next_samples(count) for gen in self._signal_gens]
        return np.sum(signals, axis=0) / len(self._signal_gens)

    @classmethod
    def blank(cls, count: int, sample_rate: int = 48000) -> Self:
        return cls(freqs=[440] * count, sample_rate=sample_rate)

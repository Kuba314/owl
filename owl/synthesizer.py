from dataclasses import dataclass

import numpy as np
import pyaudio


@dataclass
class Synthesizer:
    rate: int

    def synthesize(self, frequency_strengths: np.ndarray, duration: int) -> np.ndarray:
        signal = np.zeros(duration * self.rate)
        frequency_count = len(frequency_strengths)
        # frequencies = np.logspace(1.8, 3.5, frequency_count)
        frequencies = [440, 440*5/4, 440*4/3, 440*3/2]
        for strength, frequency in zip(frequency_strengths, frequencies):
            time = np.arange(duration * self.rate) / self.rate
            offset = np.random.uniform(0, 2 * np.pi)
            signal += strength * np.cos(2 * np.pi * frequency * time + offset)
        return signal / frequency_count
    
    def play(self, signal: np.ndarray) -> None:
        p = pyaudio.PyAudio()

        chunk_size = 1024
        stream = p.open(
            rate=self.rate,
            channels=1,
            format=pyaudio.paFloat32,
            output=True,
            frames_per_buffer=chunk_size,
        )

        for i in range(0, len(signal), chunk_size):
            chunk = signal[i : i + chunk_size]
            stream.write(chunk.astype(np.float32).tobytes())
        stream.close()




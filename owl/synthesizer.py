from dataclasses import dataclass

import numpy as np
import pyaudio


@dataclass
class Synthesizer:
    rate: int

    def synthesize(self, freq_strengths: dict[float, float], duration: int) -> np.ndarray:
        signal = np.zeros(duration * self.rate)
        for frequency, strength in freq_strengths.items():
            time = np.arange(duration * self.rate) / self.rate
            offset = np.random.uniform(0, 2 * np.pi)
            signal += strength * np.cos(2 * np.pi * frequency * time + offset)
        return signal / len(freq_strengths)
    
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




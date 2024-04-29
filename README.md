# owl
`owl` is a python project aimed at developing and evaluating the effectiveness of conversion methods from video to audio. The resulting audio could be used to learn certain method and "see" with just sound.

## Requirements
- [`poetry`](https://python-poetry.org/docs/#installation)
- `portaudio-devel` - required by `pyaudio`

## Installation
```
poetry install
```

## Converter hierarchy
The main aim of this project is to be extensible so that new converters can be easily built and integrated into the existing converter hierarchy.

Some converters are already implemented. The most simple ones are the `CurveConverter` family of converters. These converters map a space-filling curve over each frame of the input. Then the curve is walked and mapped with a frequency range. Each pixel's brightness contributes to a single sine-wave's amplitude. All sine waves (one for each pixel) are then combined into the final sound. This conversion technique is simple, but does not convey much information. It is only effective at low resolutions since higher resolutions always turn to white noise.

Another family of converters are the `ScanConverter` family of converters. These converters are dynamic, i.e. a single frame generates a sound which (unlike static converters) cannot be represented as a set of frequencies and their amplitudes. Converters of the `ScanConverter` family split the image into strips (either horizontal, vertical or circular). Then each strip is mapped with a frequency range, same as in the `CurveConverter` family. Each strip's sound is then sequentially played for each frame. A sound cue may be inserted at the start of each frame to signify a frame start to the user.

## Examples
```shell
# each frame walked by hilbert curve of order 1 (2x2)
poetry run owl curve hilbert

# each frame walked by peano curve of order 1 (3x3)
poetry run owl curve peano

# every frame (each 500ms) gets scanned with 4 circles all having 4 samples on each circle
poetry run owl scan circular -c4 -n4 --ms-per-frame 500

# every frame (each 100ms) gets scanned column-wise left to right, 4 columns each having 4 samples
poetry run owl scan horizontal -c4 -n4 --ms-per-frame 100
```

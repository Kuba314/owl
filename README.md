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

## Running on Windows
The project should work out of the box, but there might be some issues with building or running of `pyaudio` or `portaudio`. To workaround this issue, the application can be run in WSL by sending sound through pulse audio to a pulseaudio server on windows. Follow the instructions at [microsoft/WSL#5816 (comment)](https://github.com/microsoft/WSL/issues/5816#issuecomment-682242686), specifically:
1. On Windows, download pulseaudio from http://code.x2go.org/releases/binary-win32/3rd-party/pulse/pulseaudio-5.0-rev18.zip and extract it
2. Insert the following text into a `config.pa` file in the `pulse` directory:
```
load-module module-native-protocol-tcp auth-anonymous=1
load-module module-esound-protocol-tcp auth-anonymous=1
load-module module-waveout sink_name=output source_name=input record=0
```
3. Run pulseaudio with `pulseaudio.exe -F config.pa` from within the `pulse` directory
4. On WSL, run `export PULSE_SERVER=tcp:WINDOWS_HOST_IP`, where `WINDOWS_HOST_IP` is an IP obtainable with `ipconfig` on Windows

This workaround will work as long as the Windows pulseaudio server is running and the WSL shell environment contains the `PULSE_SERVER` variable. To enable a permanent solution, please see the previously linked comment.
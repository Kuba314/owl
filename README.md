## owl
Convert images to sound.

### Requirements
- [`poetry`](https://python-poetry.org/docs/#installation)
- `portaudio-devel` - required by `pyaudio`

### Installation
```
poetry install
```

### Examples
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

A experimental Python library for composing MIDI with pipeline-based patterns.

### Core Concepts

We count time in fraction of full notes, represented as `Fraction` objects from Python's built-in `fractions` module. `ppq` (pulses per quarter note) is needed when converting from MIDI ticks to `Fraction`. `tempo` (microseconds per quarter note) is needed when playing back MIDI data.

- `Note`: Essentially `(duration : Fraction, note : int, velocity : int)`.
- `Pattern`: A series of `Note`s indexed by their `start_time`, with efficient insertion / deletion / modification / iteration, with a `duration : Fraction` attribute.
- `Modifier`: An abstract base class for all modifiers, with a `forward` method that takes one or more `Pattern` objects and returns a new `Pattern` object.

- `ProgramChange`: Essentially `(program : int)`, specifying an instrument.
- `Timeline`: Arrangement of `Pattern`s and `ProgramChange`s on the time axis and the channel axis. Responsible for rendering the final MIDI track and playback controls.

### Limitations

To keep things simple, the library currently only supports 
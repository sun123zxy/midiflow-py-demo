A experimental Python library for composing MIDI with pipeline-based patterns.

### Core Concepts

We count time in fraction of full notes, represented as `Fraction` objects from Python's built-in `fractions` module. `ppq` (pulses per quarter note) is needed when converting from MIDI ticks to `Fraction`. `tempo` (microseconds per quarter note) is needed when playing back MIDI data.

- `Note`: Essentially `(duration : Fraction, note : int, velocity : int)`.
- `Pattern`: A series of `Note`s indexed by their `start_time`, with efficient insertion / deletion / modification / iteration, with a `duration : Fraction` attribute.
- `Modifier`: An abstract base class for all modifiers, with a `forward` method that takes one or more `Pattern` objects and returns a new `Pattern` object.

- `ProgramChange`: Essentially `(program : int)`, specifying an instrument.
- `Timeline`: Arrangement of `Pattern`s and `ProgramChange`s on the time axis and the channel axis. Responsible for rendering the final MIDI track and playback controls.

### Limitations

To keep things simple, the library is currently designed to work statelessly: everything is immutable. But a comprehensive DAW has to be persistent, supporting user interactions. This includes having a directed acyclic graph of patterns and modifiers, with dynamic synthesis and caching mechanisms. This seems out of scope for this library.

It is, however, possible to have some visualization via Matplotlib. Also, to have some text-based score representation. This is left as future work.
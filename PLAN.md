To build a MIDI editor with emphasis on reusable, extensible, pipeline-based patterns.

## Data Representation

We first need to define how MIDI data and modifiers are represented in the application. For this part the task is to implement a Python library to reflect the core concepts.

### Core Concepts

We count time in fraction of full notes, represented as `Fraction` objects from Python's built-in `fractions` module. `ppq` (pulses per quarter note) is needed when converting from MIDI ticks to `Fraction`. `tempo` (microseconds per quarter note) is needed when playing back MIDI data.

- `Note`: Essentially `(duration : Fraction, note : int, velocity : int)`.
- `Pattern`: A series of `Note`s indexed by their `start_time`, with efficient insertion / deletion / modification / iteration, with a `duration : Fraction` attribute.
- `Modifier`: An abstract base class for all modifiers, with a `forward` method that takes one or more `Pattern` objects and returns a new `Pattern` object.

- `PatternFlowNode`: A node in the `PatternFlow` graph.
- `PatternFlow`: A directed acyclic graph (DAG) with nodes and edges representing flow synthesis of patterns.

- `ProgramChange`: Essentially `(program : int)`, specifying an instrument.
- `Timeline`: Arrangement of `PatternFlowNode` objects and `ProgramChange` on the time axis and the channel axis.

### Pattern

See code.

### Modifier

See code.

### PatternFlow

See code.

### Timeline

Responsible for rendering the final MIDI track and playback controls. 

- `tempo : int = 500000`: Microseconds per quarter note.
- `flow : PatternFlow`
- `canvas : dict[Tuple[Fraction, int], str | ProgramChange]`
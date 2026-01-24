### Timeline

Responsible for rendering the final MIDI track and playback controls. 

- `tempo : int = 500000`: Microseconds per quarter note.
- `flow : PatternFlow`
- `canvas : dict[Tuple[Fraction, int], str | ProgramChange]`
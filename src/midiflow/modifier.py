from fractions import Fraction
from typing import Annotated
from pydantic import BaseModel, Field
from .pattern import Pattern, Note


class Modifier(BaseModel):
    """Abstract base class for all modifiers.
    
    Think of `nn.Module` objects in PyTorch that can be pipelined together to create neural networks.
    Each module has a `forward` method that defines how pattern flows through it.
    We adopt a similar design here:
    Miltiple input patterns, one output pattern, with possible parameters initialized in the constructor.

    `mf.Modifier` is an abstract base class. Specific modifiers should inherit from this class,
    implement their forward method to define their transformation logic.
    Since we are using Pydantic, parameters can be defined as class attributes with type annotations,
    so a constructor is automatically generated.
    """

    def forward(self, *patterns: Pattern, **kwargs: Pattern) -> Pattern:
        """Transform input patterns to produce an output pattern. """
        pass

    def __call__(self, *patterns: Pattern, **kwargs: Pattern) -> Pattern:
        """Make the modifier callable, delegating to forward method."""
        return self.forward(*patterns, **kwargs)

class FromPattern(Modifier):
    """Simply returns a predefined pattern."""

    pattern: Pattern

    def forward(self) -> Pattern:
        return self.pattern

class Union(Modifier):
    """Combine a list of patterns into one by merging their notes, aligned by start time 0."""
    
    def forward(self, *patterns: Pattern) -> Pattern:
        if not patterns: return Pattern()
        max_duration = max(pattern.duration for pattern in patterns)
        notes : dict[Fraction, list[Note]] = {}
        for pattern in patterns:
            for start_time, chord in pattern.notes.items():
                if start_time not in notes:
                    notes[start_time] = []
                notes[start_time].extend(chord)
        return Pattern(notes=notes, duration=max_duration)

class Concat(Modifier):
    """Concatenate a list of patterns end-to-end."""
    
    def forward(self, *patterns: Pattern) -> Pattern:
        if not patterns: return Pattern()
        duration = Fraction(0)
        notes : dict[Fraction, list[Note]] = {}
        for pattern in patterns:
            for start_time, chord in pattern.notes.items():
                new_start_time = duration + start_time
                if new_start_time not in notes:
                    notes[new_start_time] = []
                notes[new_start_time].extend(chord)
            duration += pattern.duration
        return Pattern(notes=notes, duration=duration)

class Trim(Modifier):
    """Trimming a pattern to make sure `start_time` of notes are within `[0, duration]`.
    
    When optional parameter `trim_end=False` set to `True`, will also trim notes that exceed the pattern's duration.
    """
    
    trim_end: bool = False
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            if start_time < 0 or start_time > pattern.duration:
                continue
            if self.trim_end: # Trim notes that exceed pattern duration
                for note in chord:
                    if start_time + note.duration > pattern.duration:
                        note.duration = max(Fraction(0), pattern.duration - start_time)
            notes[start_time] = chord
        return Pattern(notes=notes, duration=pattern.duration)

class View(Modifier):
    """Adjust the time window of the pattern.

    If `start_time` is not zero, shift the pattern's zero time pointer to `start_time`.
    Set the pattern's duration to `end_time - start_time`. Note that this modifier won't discard any notes.
    """
    
    start_time: Fraction = Fraction(0)
    end_time: Fraction | None = None
    
    def forward(self, pattern: Pattern) -> Pattern:
        if not self.end_time :
            self.end_time = pattern.duration
        if self.start_time == 0 :
            return Pattern(notes=pattern.notes, duration=self.end_time)

        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time - self.start_time] = chord
        duration = self.end_time - self.start_time
        return Pattern(notes=notes, duration=duration)

class Stretch(Modifier):
    """Stretch or compress the whole pattern by a specified factor."""
    
    factor: Annotated[Fraction, Field(ge=0)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time * self.factor] = [
                Note(duration=note.duration * self.factor, note=note.note, velocity=note.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration * self.factor)

class ScaleVelocity(Modifier):
    """Scale the velocity of all notes by a specified factor."""
    
    factor: Annotated[float, Field(ge=0)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=note.duration, note=note.note, 
                     velocity=max(0, min(127, int(note.velocity * self.factor))))
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class SetVelocity(Modifier):
    """Set the velocity of all notes to a specified value."""
    
    velocity: Annotated[int, Field(ge=0, le=127)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=note.duration, note=note.note, velocity=self.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class ScaleDuration(Modifier):
    """Scale the duration of all notes by a specified factor."""
    
    factor: Annotated[Fraction, Field(ge=0)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=note.duration * self.factor, note=note.note, velocity=note.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class SetDuration(Modifier):
    """Set the duration of all notes to a specified value."""
    
    duration: Annotated[Fraction, Field(ge=0)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=self.duration, note=note.note, velocity=note.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class Transpose(Modifier):
    """Transpose all notes by a specified number of semitones."""
    
    semitones: Annotated[int, Field(ge=-127, le=127)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=note.duration, 
                     note=max(0, min(127, note.note + self.semitones)), 
                     velocity=note.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class Reverse(Modifier):
    """Reverse the order of notes in time.
    
    That is, reverse the time axis and set the zero point at `duration`.
    """
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[pattern.duration - start_time] = chord
        return Pattern(notes=notes, duration=pattern.duration)

class Invert(Modifier):
    """Invert the pitches of notes around a specified center pitch."""
    
    center_pitch: Annotated[int, Field(ge=0, le=127)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            notes[start_time] = [
                Note(duration=note.duration, 
                     note=max(0, min(127, 2 * self.center_pitch - note.note)), 
                     velocity=note.velocity)
                for note in chord
            ]
        return Pattern(notes=notes, duration=pattern.duration)

class Quantize(Modifier):
    """Quantize all message time to the nearest specified grid."""
    
    denominator: Annotated[int, Field(gt=0)]
    
    def forward(self, pattern: Pattern) -> Pattern:
        notes : dict[Fraction, list[Note]] = {}
        for start_time, chord in pattern.notes.items():
            quantized_time = start_time.limit_denominator(self.denominator)
            notes[quantized_time] = chord
        return Pattern(notes=notes, duration=pattern.duration)

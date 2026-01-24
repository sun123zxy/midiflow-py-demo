from fractions import Fraction
from typing import Self, Annotated
from pydantic import BaseModel, Field, model_validator, PrivateAttr
from mido import MidiFile, MidiTrack

class Note(BaseModel):
    """A single note with duration, note and velocity."""
    duration: Annotated[Fraction, Field(default=Fraction(1, 4), ge=0)]
    note: Annotated[int, Field(default=0, ge=0, le=127)]
    velocity: Annotated[int, Field(default=64, ge=0, le=127)]

class Pattern(BaseModel):
    """A series of `Note`s indexed by their `start_time` along with a `duration` attribute.

    Designed for efficient modification.

    Start time can be negative or greater than `duration`.
    This allows for easy alignment when combining patterns:
    as if the pattern is occupying the time range `[0, duration)`.
    """
    notes: Annotated[list[tuple[Fraction, Note]], Field(default_factory=list)]
    duration: Annotated[Fraction | None, Field(default=None)]

    _real_start_time: Fraction = PrivateAttr()
    _real_end_time: Fraction = PrivateAttr()

    @model_validator(mode='after')
    def post_validation(self) -> Self:
        self.notes = sorted(self.notes, key=lambda x: x[0])
        if self.duration is None:
            self.duration = max((start_time + note.duration for start_time, note in self.notes), default=Fraction(0))
        
        self._real_start_time = min((start_time for start_time, _ in self.notes), default=Fraction(0))
        self._real_end_time = max((start_time + note.duration for start_time, note in self.notes), default=Fraction(0))
        return self
    
    @property
    def real_start_time(self) -> Fraction:
        return self._real_start_time
    
    @property
    def real_end_time(self) -> Fraction:
        return self._real_end_time

    @classmethod
    def from_track(cls, track : MidiTrack, ppq: Annotated[int, Field(default=480, ge=0)]) -> Self:
        active_notes: dict[tuple[int, int, int], Fraction] = {}
        current_time = Fraction(0)
        pattern : dict[Fraction, list[Note]] = {}
        
        for msg in track:
            current_time += Fraction(msg.time, ppq * 4)
            if msg.type == 'note_on':
                active_notes[(msg.channel, msg.note, msg.velocity)] = current_time
            elif msg.type == 'note_off':
                key = (msg.channel, msg.note, msg.velocity)
                if key in active_notes:
                    start_time = active_notes.pop(key)
                    duration = current_time - start_time
                    note = Note(duration=duration, note=msg.note, velocity=msg.velocity)
                    if start_time not in pattern:
                        pattern[start_time] = []
                    pattern[start_time].append(note)
        
        # resolve notes that are still active at the end of the track
        for (channel, note_num, velocity), start_time in active_notes.items():
            duration = current_time - start_time
            note = Note(duration=duration, note=note_num, velocity=velocity)
            if start_time not in pattern:
                pattern[start_time] = []
            pattern[start_time].append(note)
        
        return Pattern(notes = pattern, duration = current_time)

    @classmethod
    def from_filepath(cls, filepath : str) -> Self:
        """Load pattern from a MIDI file. Merges all tracks into one, using the file's PPQ."""
        file = MidiFile(filepath)
        return cls.from_track(file.merged_track, ppq=file.ticks_per_beat)

from fractions import Fraction
from typing import Annotated
from pydantic import BaseModel, Field
from mido import MidiFile, MidiTrack, Message, MetaMessage, open_output

from .pattern import Pattern

class ProgramChange(BaseModel):
    """MIDI program change (instrument selection)."""
    program: Annotated[int, Field(default=0, ge=0, le=127)]

class PlaybackConfig(BaseModel):
    tempo: Annotated[int, Field(default=500000, gt=0, description="Microseconds per quarter note")]
    ppq: Annotated[int, Field(default=480, gt=0, description="Pulses (ticks) per quarter note")]
    start_time : Annotated[Fraction, Field(default=Fraction(0), ge=0, description="Start time in quarter notes")]
    end_time : Annotated[Fraction | None, Field(default=None, ge=0, description="End time in quarter notes")]
    default_programs: Annotated[dict[int, int],
                                Field(default_factory=lambda: {channel : 0 for channel in range(16)},
                                      description="Default program changes per channel")]

class Timeline(BaseModel):
    """Timeline for rendering and playing back MIDI patterns.
    
    The canvas maps (start_time, channel) to Pattern or ProgramChange objects.
    """
    canvas: Annotated[list[tuple[Fraction, int, Pattern | ProgramChange]], Field(default_factory=list)]
    
    def to_track(self, config : PlaybackConfig) -> MidiTrack:
        """Render the timeline into a single `mido.MidiTrack`."""
        events : list[tuple[Fraction, int, Message]] = []
        for time, channel, item in self.canvas:
            if isinstance(item, Pattern):
                for start_time, note in item.notes:
                    if time + start_time >= config.start_time and (config.end_time is None or time + start_time < config.end_time):
                        events.append((time + start_time, channel,
                                       Message('note_on', note=note.note, velocity=note.velocity)))
                        events.append((time + start_time + note.duration, channel,
                                       Message('note_off', note=note.note, velocity=note.velocity)))
            elif isinstance(item, ProgramChange):
                track.append(Message('program_change', program=item.program, channel=channel))        
        events = sorted(events, key=lambda e: (e[0], e[1]))
        track = MidiTrack()
        track.append(MetaMessage('set_tempo', tempo=config.tempo, time=0))
        current_time = config.start_time
        for time, channel, msg in events:
            delta_time = time - current_time
            msg.time = int(delta_time * config.ppq * 4)
            track.append(msg)
            current_time = time
        return track

    def to_file(self, config : PlaybackConfig) -> MidiFile:
        """Render the timeline into a `mido.MidiFile`."""
        file = MidiFile(ticks_per_beat=config.ppq)
        track = self.to_track(config)
        file.tracks.append(track)
        return file

    def save(self, filename : str, config : PlaybackConfig) -> None:
        """Save the rendered timeline to a MIDI file."""
        file = self.to_file(config)
        file.save(filename)
    
    def play(self, config : PlaybackConfig) -> None:
        """Play back the timeline."""
        file = self.to_file(config)
        with open_output() as op:
            for msg in file.play():
                op.send(msg)
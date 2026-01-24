from fractions import Fraction
import pytest
from midiflow.pattern import Note, Pattern


def test_note_creation():
    """Test Note model creation with defaults and custom values."""
    note = Note()
    assert note.duration == Fraction(1, 4)
    assert note.note == 0
    assert note.velocity == 64
    
    custom_note = Note(duration=Fraction(1, 2), note=60, velocity=100)
    assert custom_note.duration == Fraction(1, 2)
    assert custom_note.note == 60
    assert custom_note.velocity == 100


def test_note_validation():
    """Test Note model field validation."""
    with pytest.raises(Exception):  # negative duration
        Note(duration=Fraction(-1, 4))
    
    with pytest.raises(Exception):  # note out of range
        Note(note=128)
    
    with pytest.raises(Exception):  # velocity out of range
        Note(velocity=128)


def test_pattern_empty():
    """Test empty Pattern behavior."""
    pattern = Pattern(notes={}, duration=Fraction(1))
    assert pattern.duration == Fraction(1)
    assert pattern.real_start_time == Fraction(0)
    assert pattern.real_end_time == Fraction(0)


def test_pattern_basic():
    """Test Pattern with basic notes."""
    notes = {
        Fraction(0): [Note(duration=Fraction(1, 4), note=60, velocity=80)],
        Fraction(1, 4): [Note(duration=Fraction(1, 4), note=64, velocity=80)],
        Fraction(1, 2): [Note(duration=Fraction(1, 2), note=67, velocity=80)],
    }
    pattern = Pattern(notes=notes, duration=Fraction(1))
    
    assert pattern.duration == Fraction(1)
    assert pattern.real_start_time == Fraction(0)
    assert pattern.real_end_time == Fraction(1)  # 1/2 + 1/2


def test_pattern_real_times():
    """Test Pattern real_start_time and real_end_time calculations."""
    # Pattern with negative start time
    notes = {
        Fraction(-1, 4): [Note(duration=Fraction(1, 4), note=60)],
        Fraction(0): [Note(duration=Fraction(1, 2), note=64)],
    }
    pattern = Pattern(notes=notes, duration=Fraction(1))
    
    assert pattern.real_start_time == Fraction(-1, 4)
    assert pattern.real_end_time == Fraction(1, 2)
    
    # Pattern extending beyond duration
    notes = {
        Fraction(3, 4): [Note(duration=Fraction(1, 2), note=60)],
    }
    pattern = Pattern(notes=notes, duration=Fraction(1))
    
    assert pattern.real_end_time == Fraction(5, 4)  # 3/4 + 1/2


def test_pattern_chord():
    """Test Pattern with simultaneous notes (chord)."""
    notes = {
        Fraction(0): [
            Note(duration=Fraction(1), note=60, velocity=80),
            Note(duration=Fraction(1), note=64, velocity=80),
            Note(duration=Fraction(1), note=67, velocity=80),
        ]
    }
    pattern = Pattern(notes=notes, duration=Fraction(1))
    
    assert len(pattern.notes[Fraction(0)]) == 3
    assert pattern.real_end_time == Fraction(1)

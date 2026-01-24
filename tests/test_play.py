from fractions import Fraction
import midiflow as mf

config = mf.PlaybackConfig(tempo=500000, ppq=480)

pitches1 = [60, 65, 67, 70, 67, 65]
pitches2 = [62, 63, 62, 58]

pattern1 = mf.Pattern(notes=[
    (Fraction(i,8), mf.Note(note=pitch, duration="1/4", velocity=100)) for i, pitch in enumerate(pitches1)
], duration = Fraction(len(pitches1),8))
pattern2 = mf.Pattern(notes=[
    (Fraction(i,8), mf.Note(note=pitch, duration="1/4", velocity=100)) for i, pitch in enumerate(pitches2)
], duration = Fraction(len(pitches2),8))

pattern1112 = mf.Concat()(pattern1, pattern1, pattern1, pattern2)
pattern1112f = mf.Concat()(pattern1112, mf.Invert(pivot=60)(mf.Reverse()(pattern1112)))

timeline = mf.Timeline(canvas=[
    (0, 0, pattern1112f),
    ("11/4", 0, mf.ProgramChange(program=40))
])

timeline.play(config)

"""
A5- D5_ F5=
  _   _   _
"""
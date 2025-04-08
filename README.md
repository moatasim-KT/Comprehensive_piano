# Comprehensive Piano

A feature-rich piano learning and visualization application that allows users to play along with MIDI files, practice scales and chords, and visualize piano performances.

## Features

- **MIDI Playback**: Load and play MIDI files with visual piano key representation
- **Play-Along Mode**: Practice playing along with MIDI files at your own pace
- **Piano Visualization**: Real-time visualization of piano keystrokes
- **MIDI Input Support**: Connect your MIDI keyboard for interactive playing
- **Music Theory Tools**: Utilities to help understand music theory concepts

## Music Theory Tools

The application includes the following music theory tools to help users understand and practice musical concepts:

### Scale Generator

The Scale Generator creates musical scales based on a root note. Available scale types include:

- Major (`major`)
- Natural Minor (`natural_minor`)
- Harmonic Minor (`harmonic_minor`)
- Melodic Minor (`melodic_minor`)
- Chromatic (`chromatic`)

**Usage Example:**
```python
from Playalong_MIDI import MusicTheory

# Generate a C major scale over 1 octave (MIDI notes)
c_major_scale = MusicTheory.generate_scale(root_note=60, scale_type="major", octaves=1)
# Result: [60, 62, 64, 65, 67, 69, 71, 72]

# Generate an A minor scale over 2 octaves
a_minor_scale = MusicTheory.generate_scale(root_note=57, scale_type="natural_minor", octaves=2)
```

### Chord Generator

The Chord Generator creates chords based on a root note. Available chord types include:

- Major (`maj`)
- Minor (`min`)
- Diminished (`dim`)
- Augmented (`aug`)
- Major 7th (`maj7`)
- Minor 7th (`min7`)
- Dominant 7th (`dom7`)
- Diminished 7th (`dim7`)
- Suspended 4th (`sus4`)

**Usage Example:**
```python
from Playalong_MIDI import MusicTheory

# Generate a C major chord (MIDI notes)
c_major_chord = MusicTheory.generate_chord(root_note=60, chord_type="maj")
# Result: [60, 64, 67]

# Generate a G dominant 7th chord
g_dom7_chord = MusicTheory.generate_chord(root_note=55, chord_type="dom7")
# Result: [55, 59, 62, 65]
```

## MIDI Note Reference

The application uses MIDI note numbers to represent piano keys:
- Middle C (C4) = MIDI note 60
- Each octave spans 12 MIDI notes
- Note range typically covers MIDI notes 21 (A0) to 108 (C8)

## Getting Started

1. Ensure you have Python 3.x installed
2. Install required dependencies:
   ```
   pip install pygame mido numpy sounddevice soundfile scipy
   ```
3. Run one of the main scripts:
   ```
   python playback.py
   python play_along.py
   python Piano_Visualizer_Optimized.py
   ```

## Modes

- **Freestyle Mode**: Play freely on the piano
- **Learning Mode**: Practice scales and chords with visual guidance
- **Play-Along Mode**: Play along with MIDI files
- **Analysis Mode**: Analyze MIDI files for musical patterns and structure

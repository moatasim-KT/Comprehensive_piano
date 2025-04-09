"""
Music Theory module for the Comprehensive Piano Application
Handles scales, chords, and other music theory concepts
"""
import logging
from typing import List, Dict, Any
import random

class MusicTheory:
    """Helper class for basic music theory elements."""

    SCALE_INTERVALS = {
        "major": [0, 2, 4, 5, 7, 9, 11, 12],  # W-W-H-W-W-W-H
        "natural_minor": [0, 2, 3, 5, 7, 8, 10, 12],  # W-H-W-W-H-W-W
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11, 12],  # W-H-W-W-H-WH-H
        "melodic_minor": [0, 2, 3, 5, 7, 9, 11, 12],  # ascending only
        "pentatonic_major": [0, 2, 4, 7, 9, 12],  # Major pentatonic
        "pentatonic_minor": [0, 3, 5, 7, 10, 12],  # Minor pentatonic
        "blues": [0, 3, 5, 6, 7, 10, 12],  # Blues scale
        "chromatic": list(range(13)),  # All 12 semitones
        "dorian": [0, 2, 3, 5, 7, 9, 10, 12],  # W-H-W-W-W-H-W
        "phrygian": [0, 1, 3, 5, 7, 8, 10, 12],  # H-W-W-W-H-W-W
        "lydian": [0, 2, 4, 6, 7, 9, 11, 12],  # W-W-W-H-W-W-W
        "mixolydian": [0, 2, 4, 5, 7, 9, 10, 12],  # W-W-H-W-W-H-W
    }
    
    CHORD_INTERVALS = {
        "maj": [0, 4, 7],  # Major Triad
        "min": [0, 3, 7],  # Minor Triad
        "dim": [0, 3, 6],  # Diminished Triad
        "aug": [0, 4, 8],  # Augmented Triad
        "maj7": [0, 4, 7, 11],  # Major 7th
        "min7": [0, 3, 7, 10],  # Minor 7th
        "dom7": [0, 4, 7, 10],  # Dominant 7th
        "dim7": [0, 3, 6, 9],  # Diminished 7th
        "half_dim": [0, 3, 6, 10],  # Half-diminished 7th
        "sus2": [0, 2, 7],  # Suspended 2nd
        "sus4": [0, 5, 7],  # Suspended 4th
        "add9": [0, 4, 7, 14],  # Add 9th
        "add11": [0, 4, 7, 17],  # Add 11th
        "maj9": [0, 4, 7, 11, 14],  # Major 9th
        "min9": [0, 3, 7, 10, 14],  # Minor 9th
        "dom9": [0, 4, 7, 10, 14],  # Dominant 9th
        "maj11": [0, 4, 7, 11, 14, 17],  # Major 11th
        "min11": [0, 3, 7, 10, 14, 17],  # Minor 11th
        "dom11": [0, 4, 7, 10, 14, 17],  # Dominant 11th
        "maj13": [0, 4, 7, 11, 14, 17, 21],  # Major 13th
        "min13": [0, 3, 7, 10, 14, 17, 21],  # Minor 13th
        "dom13": [0, 4, 7, 10, 14, 17, 21],  # Dominant 13th
        "aug7": [0, 4, 8, 10],  # Augmented 7th
        "minMaj7": [0, 3, 7, 11],  # Minor Major 7th
    }
    
    COMMON_PROGRESSIONS = {
        "I-IV-V": [0, 5, 7],  # C-F-G in C major
        "I-V-vi-IV": [0, 7, 9, 5],  # C-G-Am-F in C major
        "ii-V-I": [2, 7, 0],  # Dm-G-C in C major
        "I-vi-IV-V": [0, 9, 5, 7],  # C-Am-F-G in C major
        "vi-IV-I-V": [9, 5, 0, 7],  # Am-F-C-G in C major
        "I-IV-vi-V": [0, 5, 9, 7],  # C-F-Am-G in C major
        "I-V-vi-iii-IV-I-IV-V": [0, 7, 9, 4, 5, 0, 5, 7],  # Extended progression
        "I-ii-V": [0, 2, 7], # C-Dm-G in C major
        "I-vi-ii-V": [0, 9, 2, 7], # C-Am-Dm-G in C major
        "I-bVII-IV": [0, 10,5], # C-Bb-F in C major (bluesy)
    }

    @staticmethod
    def generate_scale(
        root_note: int, scale_type: str = "major", octaves: int = 1
    ) -> List[int]:
        """Generates MIDI notes for a scale.
        
        Args:
            root_note (int): MIDI note number of the root note
            scale_type (str): Type of scale (e.g., 'major', 'natural_minor')
            octaves (int): Number of octaves to generate
            
        Returns:
            List[int]: List of MIDI note numbers in the scale
        """
        intervals = MusicTheory.SCALE_INTERVALS.get(scale_type.lower())
        if not intervals:
            logging.warning(f"Unknown scale type: {scale_type}. Defaulting to major.")
            intervals = MusicTheory.SCALE_INTERVALS["major"]

        scale_notes = []
        for o in range(octaves):
            for interval in intervals[:-1]:  # Exclude octave repetition within loop
                note = root_note + (o * 12) + interval
                if 0 <= note <= 127:
                    scale_notes.append(note)
        # Add the final octave note
        final_note = root_note + (octaves * 12)
        if 0 <= final_note <= 127:
            scale_notes.append(final_note)

        return scale_notes

    @staticmethod
    def generate_chord(root_note: int, chord_type: str = "maj", inversion: int = 0) -> List[int]:
        """Generates MIDI notes for a chord with a specific inversion.
        
        Args:
            root_note (int): MIDI note number of the root note
            chord_type (str): Type of chord (e.g., 'maj', 'min7')
            inversion (int): Inversion number (0 for root, 1 for first, 2 for second, etc.)
            
        Returns:
            List[int]: List of MIDI note numbers in the chord
        """
        intervals = MusicTheory.CHORD_INTERVALS.get(chord_type.lower())
        if not intervals:
            logging.warning(
                f"Unknown chord type: {chord_type}. Defaulting to major triad."
            )
            intervals = MusicTheory.CHORD_INTERVALS["maj"]

            num_intervals = len(intervals)
        if inversion > 0:
            if inversion >= num_intervals:
                logging.warning(
                    f"Inversion number {inversion} too high for chord type {chord_type}. Defaulting to root position."
                )
                inversion = 0
            intervals = intervals[inversion:] + [intervals[i] + 12 for i in range(inversion)]

        chord_notes = []
        for interval in intervals:
            note = root_note + interval
            if 0 <= note <= 127:
                chord_notes.append(note)
        return chord_notes
    
    @staticmethod
    def _generate_algorithmic_progression(scale_type: str = "major", mood: str = "neutral", complexity: str = "medium", length: int = 4) -> List[int]:
        """Generates a chord progression algorithmically based on musical rules.

        For this basic implementation, we simply select a random progression from a predefined set
        based on the scale type.

        Args:
            scale_type (str): Type of scale to base the progression on.
            mood (str): Mood of the progression (currently unused).
            complexity (str): Complexity of the progression (currently unused).
            length (int): Length of the progression in chords.

        Returns:
            List[int]: List of scale degrees representing the chord progression.
        """
        progressions_by_scale = {
            "major": {
                "happy": {
                    "simple": [[0, 5, 7, 0], [0, 7, 9, 5]],  # I-IV-V-I, I-V-vi-IV
                    "complex": [[2, 7, 0], [0, 5, 9, 7]]  # ii-V-I, I-IV-vi-V
                },
                "sad": {
                    "simple": [[0, 3, 5, 0], [9, 5, 0, 2]],  # i-iv-VI-i, vi-IV-i-ii
                    "complex": [[0, 3, 7, 5], [0, 5, 7, 0]]  # i-iv-VII-VI, i-IV-V-i
                }
            },
            "natural_minor": {
                "happy": {
                    "simple": [[0, 3, 5, 0], [9, 5, 0, 2]],  # i-iv-VI-i, vi-IV-i-ii
                    "complex": [[0, 3, 7, 5], [0, 5, 7, 0]]  # i-iv-VII-VI, i-IV-V-i
                },
                "sad": {
                    "simple": [[0, 3, 5, 0], [9, 5, 0, 8]],  # i-iv-VI-I, vi-IV-i-bIII
                    "complex": [[0, 2, 3, 4], [0, 5, 7, 0]]  # i-ii-III-IV, i-VI-V-I
                }
            },
            # Add more scales, moods, and complexities as needed
        }

        mood_progressions = progressions_by_scale.get(scale_type, {}).get(mood, {})
        complexity_progressions = mood_progressions.get(complexity, [[0, 5, 7, 0]])  # Default to major progression

        scale_degrees = random.choice(complexity_progressions)
        # Adjust progression length if needed
        if len(scale_degrees) < length:
            scale_degrees = scale_degrees * (length // len(scale_degrees)) + scale_degrees[:length % len(scale_degrees)]
        elif len(scale_degrees) > length:
            scale_degrees = scale_degrees[:length]

        return scale_degrees
    
    @staticmethod
    def generate_chord_progression(
        root_note: int, progression_name: str = None, scale_type: str = "major", mood: str = "neutral", complexity: str = "medium", length: int = 4, use_inversions: bool = False
    ) -> List[List[int]]:
        """Generates a chord progression based on a scale and mood.
        
        Args:
            root_note (int): MIDI note number of the root note
            progression_name (str): Name of the progression (e.g., 'I-IV-V')
            scale_type (str): Type of scale to base the progression on
            mood (str): Mood of the progression ("happy", "sad", or "neutral")
            complexity (str): Complexity of the progression ("simple", "medium", or "complex")
            length (int): Length of the progression in chords.
            use_inversions (bool): Whether to use chord inversions (default: False)
            
        Returns:
            List[List[int]]: List of chords, each a list of MIDI note numbers
        """
        if progression_name and progression_name in MusicTheory.COMMON_PROGRESSIONS:
            # Use predefined progression
            scale_degrees = MusicTheory.COMMON_PROGRESSIONS[progression_name]
        else:
            # Generate algorithmic progression
            scale_degrees = MusicTheory._generate_algorithmic_progression(scale_type, mood, complexity, length)
        
        # Generate the full scale
        scale = MusicTheory.generate_scale(root_note, scale_type, octaves=2)
        
        # Create chords for each scale degree
        progression = []
        for degree in scale_degrees:
            if degree < len(scale):
                # Use the scale degree as the root note for the chord
                chord_root = scale[degree]
                
                # Determine chord type based on scale degree
                chord_type_map = {
                    "major": ["maj", "min", "min", "maj", "dom7", "min", "half_dim"],
                    "natural_minor": ["min", "dim", "maj", "min", "min", "maj", "maj"],
                    "harmonic_minor": ["min", "dim7", "aug7", "min", "dom7", "maj", "dim7"],
                    "melodic_minor": ["maj", "min", "aug", "maj", "dom7", "min", "min"],  # using ascending
                    "dorian": ["min7", "min7", "min7", "maj7", "min7", "min7", "min7"],
                    "phrygian": ["min", "dim", "maj", "min", "min", "dim", "min"],
                    "lydian": ["maj7", "maj7", "min7", "aug", "maj", "min7", "min7"],
                    "mixolydian": ["maj", "min", "dim", "maj", "min", "min", "dom7"]
                }
                
                available_chord_types = []
                if scale_type in chord_type_map and degree < len(chord_type_map[scale_type]):
                    possible_chords = [chord for chord in chord_type_map[scale_type][degree].split() if chord in ["maj", "min", "dom7", "maj7", "min7", "dim7", "half_dim", "maj9", "min9", "dom9", "maj11", "min11", "dom11", "maj13", "min13", "dom13"]]
                    if possible_chords:
                        chord_type = possible_chords[0]
                    else:
                        logging.warning(f"No chord mapping for scale type: {scale_type}, degree: {degree}, complexity: medium. Defaulting to major triad.")
                        chord_type = "maj"
                else:
                    logging.warning(f"No chord mapping for scale type: {scale_type}, degree: {degree}. Defaulting to major triad.")
                    chord_type = "maj"

                if mood == "happy" and "min" in chord_type:
                    chord_type = "maj"
                elif mood == "sad" and "maj" in chord_type and scale_type == "major":
                    chord_type = "min"  # Only change to minor if scale type is major. Otherwise, keep the chord type
                    
                # Generate the chord
                if use_inversions:
                    num_intervals = len(MusicTheory.CHORD_INTERVALS.get(chord_type, [0, 4, 7]))
                    inversion = random.randint(0, max(0, num_intervals - 1))
                    chord = MusicTheory.generate_chord(chord_root, chord_type, inversion)
                else:
                    chord = MusicTheory.generate_chord(chord_root, chord_type)
                progression.append(chord)
        
         # Adjust progression length if needed
        if len(progression) < length:
            # Repeat the progression to reach the desired length
            progression = (progression * (length // len(progression) + 1))[:length]
        elif len(progression) > length:
            # Truncate the progression to the desired length
            progression = progression[:length]
        
        return progression

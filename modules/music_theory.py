"""
Music Theory module for the Comprehensive Piano Application
Handles scales, chords, and other music theory concepts
"""
import logging
from typing import List, Dict, Any

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
        "half_dim7": [0, 3, 6, 10],  # Half-diminished 7th
        "sus2": [0, 2, 7],  # Suspended 2nd
        "sus4": [0, 5, 7],  # Suspended 4th
        "add9": [0, 4, 7, 14],  # Add 9th
        "add11": [0, 4, 7, 17],  # Add 11th
        "maj9": [0, 4, 7, 11, 14],  # Major 9th
        "min9": [0, 3, 7, 10, 14],  # Minor 9th
        "dom9": [0, 4, 7, 10, 14],  # Dominant 9th
    }
    
    COMMON_PROGRESSIONS = {
        "I-IV-V": [0, 5, 7],  # C-F-G in C major
        "I-V-vi-IV": [0, 7, 9, 5],  # C-G-Am-F in C major
        "ii-V-I": [2, 7, 0],  # Dm-G-C in C major
        "I-vi-IV-V": [0, 9, 5, 7],  # C-Am-F-G in C major
        "vi-IV-I-V": [9, 5, 0, 7],  # Am-F-C-G in C major
        "I-IV-vi-V": [0, 5, 9, 7],  # C-F-Am-G in C major
        "I-V-vi-iii-IV-I-IV-V": [0, 7, 9, 4, 5, 0, 5, 7],  # Extended progression
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
    def generate_chord(root_note: int, chord_type: str = "maj") -> List[int]:
        """Generates MIDI notes for a chord.
        
        Args:
            root_note (int): MIDI note number of the root note
            chord_type (str): Type of chord (e.g., 'maj', 'min7')
            
        Returns:
            List[int]: List of MIDI note numbers in the chord
        """
        intervals = MusicTheory.CHORD_INTERVALS.get(chord_type.lower())
        if not intervals:
            logging.warning(
                f"Unknown chord type: {chord_type}. Defaulting to major triad."
            )
            intervals = MusicTheory.CHORD_INTERVALS["maj"]

        chord_notes = []
        for interval in intervals:
            note = root_note + interval
            if 0 <= note <= 127:
                chord_notes.append(note)
        return chord_notes
    
    @staticmethod
    def _parse_roman_numeral(numeral: str) -> int:
        """Convert a Roman numeral to a scale degree (0-based).
        
        Args:
            numeral (str): Roman numeral (e.g., 'I', 'ii', 'V')
            
        Returns:
            int: Scale degree (0-based)
        """
        numeral_map = {
            "I": 0, "i": 0,
            "II": 2, "ii": 2,
            "III": 4, "iii": 4,
            "IV": 5, "iv": 5,
            "V": 7, "v": 7,
            "VI": 9, "vi": 9,
            "VII": 11, "vii": 11
        }
        return numeral_map.get(numeral, 0)  # Default to tonic if not found
    
    @staticmethod
    def _get_scale_degrees_from_progression(progression_name: str) -> List[int]:
        """Extract scale degrees from a progression name.
        
        Args:
            progression_name (str): Name of the progression (e.g., 'I-IV-V')
            
        Returns:
            List[int]: List of scale degrees (0-based)
        """
        # Use predefined progression if available
        if progression_name in MusicTheory.COMMON_PROGRESSIONS:
            return MusicTheory.COMMON_PROGRESSIONS[progression_name]
        
        # Parse progression string (e.g., "I-IV-V" -> [0, 5, 7])
        try:
            return [MusicTheory._parse_roman_numeral(numeral) 
                   for numeral in progression_name.split('-')]
        except Exception as e:
            logging.warning(f"Failed to parse progression '{progression_name}': {e}")
            # Default to I-IV-V progression
            return MusicTheory.COMMON_PROGRESSIONS["I-IV-V"]
    
    @staticmethod
    def _determine_chord_type(scale_type: str, degree: int) -> str:
        """Determine the chord type based on scale type and degree.
        
        Args:
            scale_type (str): Type of scale (e.g., 'major', 'natural_minor')
            degree (int): Scale degree (0-based)
            
        Returns:
            str: Chord type (e.g., 'maj', 'min', 'dim')
        """
        if scale_type == "major":
            if degree in [0, 3, 4]:  # I, IV, V in major
                return "maj"
            elif degree in [1, 2, 5]:  # ii, iii, vi in major
                return "min"
            elif degree == 6:  # vii in major
                return "dim"
        elif scale_type == "natural_minor":
            if degree in [2, 5, 7]:  # III, VI, VII in minor
                return "maj"
            elif degree in [0, 3, 4]:  # i, iv, v in minor
                return "min"
            elif degree == 1:  # ii in minor
                return "dim"
        
        # Default to major triad for unknown scale types or degrees
        return "maj"
    
    @staticmethod
    def generate_chord_progression(
        root_note: int, progression_name: str, scale_type: str = "major"
    ) -> List[List[int]]:
        """Generates a chord progression based on a scale.
        
        Args:
            root_note (int): MIDI note number of the root note
            progression_name (str): Name of the progression (e.g., 'I-IV-V')
            scale_type (str): Type of scale to base the progression on
            
        Returns:
            List[List[int]]: List of chords, each a list of MIDI note numbers
        """
        # Get scale degrees from progression name
        scale_degrees = MusicTheory._get_scale_degrees_from_progression(progression_name)
        
        # Generate the full scale
        scale = MusicTheory.generate_scale(root_note, scale_type, octaves=2)
        
        # Create chords for each scale degree
        progression = []
        for degree in scale_degrees:
            if degree >= len(scale):
                continue
                
            # Use the scale degree as the root note for the chord
            chord_root = scale[degree]
            
            # Determine chord type based on scale degree and scale type
            chord_type = MusicTheory._determine_chord_type(scale_type, degree)
            
            # Generate the chord and add to progression
            chord = MusicTheory.generate_chord(chord_root, chord_type)
            progression.append(chord)
        
        return progression

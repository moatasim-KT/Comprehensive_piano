#!/usr/bin/env python3
"""
Test script for the music_theory.py module
This script demonstrates the basic functionality of the MusicTheory class
"""
from modules.music_theory import MusicTheory
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def print_note_list(note_list, label="Notes"):
    """Helper to print a list of MIDI notes with a label."""
    print(f"\n{label}: {note_list}")

def main():
    print("Testing Music Theory Module Functionality")
    print("----------------------------------------")
    
    # Example 1: Generate a C major scale (C4 = MIDI note 60)
    c_major_scale = MusicTheory.generate_scale(60, "major", octaves=1)
    print_note_list(c_major_scale, "C Major Scale")
    
    # Example 2: Generate an A minor scale (A3 = MIDI note 57)
    a_minor_scale = MusicTheory.generate_scale(57, "natural_minor", octaves=1)
    print_note_list(a_minor_scale, "A Minor Scale")
    
    # Example 3: Generate a pentatonic scale
    g_pentatonic = MusicTheory.generate_scale(55, "pentatonic_major", octaves=1)
    print_note_list(g_pentatonic, "G Pentatonic Scale")
    
    # Example 4: Generate chords
    c_major_chord = MusicTheory.generate_chord(60, "maj")
    print_note_list(c_major_chord, "C Major Chord")
    
    d_minor_chord = MusicTheory.generate_chord(62, "min")
    print_note_list(d_minor_chord, "D Minor Chord")
    
    g_dominant_chord = MusicTheory.generate_chord(67, "dom7")
    print_note_list(g_dominant_chord, "G Dominant 7th Chord")
    
    # Example 5: Generate chord with inversion
    c_major_first_inversion = MusicTheory.generate_chord(60, "maj", inversion=1)
    print_note_list(c_major_first_inversion, "C Major Chord (First Inversion)")
    
    # Example 6: Generate a chord progression
    print("\nGenerating C major chord progression (I-IV-V):")
    progression = MusicTheory.generate_chord_progression(60, progression_name="I-IV-V")
    for i, chord in enumerate(progression, 1):
        print_note_list(chord, f"Chord {i}")
    
    # Example 7: Generate an algorithmic progression with specific mood
    print("\nGenerating algorithmic chord progression in A minor with sad mood:")
    sad_progression = MusicTheory.generate_chord_progression(
        57, scale_type="natural_minor", mood="sad", complexity="complex", length=4
    )
    for i, chord in enumerate(sad_progression, 1):
        print_note_list(chord, f"Chord {i}")

if __name__ == "__main__":
    main()
"""
Helper functions for the Comprehensive Piano Application
"""
import os
import pygame
import numpy as np

# Note names
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def get_note_name(note):
    """
    Get the standard note name (e.g., C#4) from MIDI note number
    
    Args:
        note (int): MIDI note number (0-127)
        
    Returns:
        str: Note name with octave (e.g., "C4", "F#5")
    """
    if not 0 <= note <= 127:
        return "Invalid"
    
    note_name = NOTE_NAMES[note % 12]
    octave = (note // 12) - 1  # MIDI note 0 is C-1, 12 is C0, etc.
    return f"{note_name}{octave}"

def is_black_key(note):
    """
    Check if a MIDI note number corresponds to a black key
    
    Args:
        note (int): MIDI note number
        
    Returns:
        bool: True if the note is a black key, False otherwise
    """
    return (note % 12) in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#

def midi_to_freq(note):
    """
    Convert MIDI note number to frequency in Hz
    
    Args:
        note (int): MIDI note number
        
    Returns:
        float: Frequency in Hz
    """
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def load_assets(asset_dir='assets'):
    """
    Load all assets from the assets directory
    
    Args:
        asset_dir (str): Path to assets directory
        
    Returns:
        dict: Dictionary of loaded assets
    """
    assets = {}
    
    # Create assets directory if it doesn't exist
    if not os.path.exists(asset_dir):
        os.makedirs(asset_dir)
        
    return assets

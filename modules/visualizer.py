"""
Piano Visualizer module for the Comprehensive Piano Application
Handles the visual representation of piano keys and notes
"""
import pygame
import pygame.midi
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from collections import defaultdict

# Import from our modules
from utils.helpers import get_note_name, is_black_key, midi_to_freq

class PianoVisualizer:
    """Core class for piano visualization and rendering."""
    
    def __init__(self, width=1600, height=600):
        """Initialize the piano visualizer.
        
        Args:
            width (int): Screen width
            height (int): Screen height
        """
        self.width = width
        self.height = height
        
        # Piano dimensions
        self.white_key_width = 40
        self.white_key_height = 220
        self.black_key_width = 24
        self.black_key_height = 140
        
        # Piano position
        self.piano_start_x = 40
        self.piano_start_y = 280
        
        # Key range - default to full 88 keys
        self.first_note = 21  # A0
        self.total_keys = 88
        
        # Note tracking
        self.active_notes = defaultdict(lambda: False)    # Notes currently being played
        self.highlighted_notes = defaultdict(lambda: False)  # Notes highlighted for learning
        self.note_colors = defaultdict(lambda: (180, 180, 255))  # Note visualization colors
        self.note_velocities = defaultdict(lambda: 127)  # Note velocities for color intensity
        
        # Fonts for drawing
        self.title_font = None
        self.font = None 
        self.key_font = None
        
        # Display options
        self.show_note_names = True
        self.show_octave_markers = True
        self.highlight_style = "fill"  # "fill", "outline", or "glow"
        
        # Key graphics cache
        self.key_rects = {}  # Cache of key rectangles by note number
    
    def initialize(self, screen):
        """Initialize the visualizer with the pygame screen.
        
        Args:
            screen: Pygame screen surface
        """
        self.screen = screen
        
        # Initialize fonts
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.font = pygame.font.SysFont("Arial", 24)
        self.key_font = pygame.font.SysFont("Arial", 16)
        
        # Build key rectangles cache
        self._build_key_rects()
    
    def _build_key_rects(self):
        """Build a cache of rectangles for all piano keys."""
        self.key_rects = {}
        
        # Calculate visible key range
        for note in range(self.first_note, self.first_note + self.total_keys):
            is_black = is_black_key(note)
            key_width = self.black_key_width if is_black else self.white_key_width
            key_height = self.black_key_height if is_black else self.white_key_height
            
            x = self.get_key_position(note)
            if x is not None:
                self.key_rects[note] = pygame.Rect(
                    x, self.piano_start_y, 
                    key_width, key_height
                )
    
    def resize(self, width, height):
        """Handle window resize events.
        
        Args:
            width (int): New screen width
            height (int): New screen height
        """
        self.width = width
        self.height = height
        
        # Adjust piano position based on new dimensions
        self.piano_start_y = int(height * 0.5)  # Piano at middle of screen
        
        # Rebuild key rectangles
        self._build_key_rects()
    
    def set_key_range(self, first_note, total_keys):
        """Set the range of piano keys to display.
        
        Args:
            first_note (int): First MIDI note number
            total_keys (int): Total number of keys to display
        """
        self.first_note = first_note
        self.total_keys = total_keys
        
        # Rebuild key rectangles
        self._build_key_rects()
    
    def get_key_position(self, note):
        """Get the x-coordinate of a piano key.
        
        Args:
            note (int): MIDI note number
            
        Returns:
            int or None: x-coordinate of the key, or None if out of range
        """
        if note < self.first_note or note >= self.first_note + self.total_keys:
            return None
        
        # Count white keys before this note
        white_key_count = len([n for n in range(self.first_note, note + 1) 
                               if not is_black_key(n)])
                               
        # Adjust for black keys
        if is_black_key(note):
            # Find previous white key
            prev_white = note - 1
            while is_black_key(prev_white) and prev_white >= self.first_note:
                prev_white -= 1
            
            # Get position of previous white key
            if prev_white < self.first_note:
                return None
                
            prev_pos = self.get_key_position(prev_white)
            if prev_pos is None:
                return None
                
            # Black key position is offset from the white key
            return prev_pos + self.white_key_width - (self.black_key_width // 2)
        else:
            # Count white keys before this note (excluding this note)
            white_keys_before = len([n for n in range(self.first_note, note) 
                                  if not is_black_key(n)])
            return self.piano_start_x + (white_keys_before * self.white_key_width)
    
    def draw_piano(self):
        """Draw the piano keyboard."""
        if not hasattr(self, 'screen'):
            logging.error("Visualizer not initialized with screen")
            return
        
        # First draw all white keys
        for note in range(self.first_note, self.first_note + self.total_keys):
            if not is_black_key(note):
                self._draw_key(note)
        
        # Then draw all black keys (on top)
        for note in range(self.first_note, self.first_note + self.total_keys):
            if is_black_key(note):
                self._draw_key(note)
        
        # Draw octave markers if enabled
        if self.show_octave_markers:
            self._draw_octave_markers()
    
    def _draw_key(self, note):
        """Draw a single piano key.
        
        Args:
            note (int): MIDI note number
        """
        is_black = is_black_key(note)
        
        # Get key position and dimensions
        if note not in self.key_rects:
            return
            
        rect = self.key_rects[note]
        
        # Determine key color based on state
        if self.active_notes[note] and self.highlighted_notes[note]:
            # Note is both active and highlighted (correct hit)
            color = (100, 255, 100)  # Bright green
        elif self.active_notes[note]:
            # Note is being played
            velocity = self.note_velocities[note]
            # Adjust brightness based on velocity
            brightness = min(255, 100 + int(155 * velocity / 127))
            color = (180, 180, brightness)  # Blue tint, brightness varies with velocity
        elif self.highlighted_notes[note]:
            # Note is highlighted for learning
            color = (255, 255, 100)  # Yellow
        else:
            # Default key color
            color = (0, 0, 0) if is_black else (255, 255, 255)
        
        # Draw the key
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw border
        border_color = (100, 100, 100) if is_black else (0, 0, 0)
        pygame.draw.rect(self.screen, border_color, rect, 1)
        
        # Draw note name if enabled
        if self.show_note_names:
            note_name = get_note_name(note)
            text_color = (255, 255, 255) if is_black else (0, 0, 0)
            name_text = self.key_font.render(note_name, True, text_color)
            
            # Position text in the lower part of the key
            text_x = rect.x + (rect.width - name_text.get_width()) // 2
            text_y = rect.y + rect.height - name_text.get_height() - 5
            
            self.screen.blit(name_text, (text_x, text_y))
    
    def _draw_octave_markers(self):
        """Draw octave markers (C notes) on the keyboard."""
        for note in range(self.first_note, self.first_note + self.total_keys):
            # Check if note is a C
            if note % 12 == 0 and note in self.key_rects:
                rect = self.key_rects[note]
                octave = note // 12 - 1  # Calculate octave (C4 = middle C)

                # Draw octave marker
                pygame.draw.rect(
                    self.screen, 
                    (200, 200, 200),  # Light gray
                    (rect.x, rect.y + rect.height, rect.width, 5)
                )

                # Draw octave number
                text = self.font.render(f"C{octave}", True, (0, 0, 0))
                self.screen.blit(
                    text, 
                    (rect.x + 2, rect.y + rect.height + 5)
                )

    
    def set_note_active(self, note, active=True, velocity=127):
        """Set a note as active or inactive.
        
        Args:
            note (int): MIDI note number
            active (bool): Whether the note is active
            velocity (int): MIDI velocity (0-127)
        """
        self.active_notes[note] = active
        if active:
            self.note_velocities[note] = velocity
    
    def set_note_highlighted(self, note, highlighted=True):
        """Set a note as highlighted or not highlighted.
        
        Args:
            note (int): MIDI note number
            highlighted (bool): Whether the note is highlighted
        """
        self.highlighted_notes[note] = highlighted
    
    def highlight_chord(self, notes, highlight=True):
        """Highlight a chord (multiple notes).
        
        Args:
            notes (List[int]): List of MIDI note numbers
            highlight (bool): Whether to highlight or unhighlight
        """
        for note in notes:
            self.set_note_highlighted(note, highlight)
    
    def clear_active_notes(self):
        """Clear all active notes."""
        self.active_notes = defaultdict(lambda: False)
    
    def clear_highlighted_notes(self):
        """Clear all highlighted notes."""
        self.highlighted_notes = defaultdict(lambda: False)
    
    def get_key_at_position(self, pos_x, pos_y):
        """Get the note at a given screen position.
        
        Args:
            pos_x (int): X-coordinate
            pos_y (int): Y-coordinate
            
        Returns:
            int or None: MIDI note number or None if no key at position
        """
        # Check each key rectangle
        for note, rect in self.key_rects.items():
            if rect.collidepoint(pos_x, pos_y):
                return note
        
        return None

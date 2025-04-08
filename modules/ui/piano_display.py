"""
Piano Display component for the Comprehensive Piano Application
Handles the rendering of the piano keyboard and visual feedback
"""
import pygame
import pygame.midi
from typing import Dict, List, Tuple, Optional, Any
import logging
from collections import defaultdict

from utils.helpers import get_note_name, is_black_key

class PianoDisplay:
    """Handles the display and interaction with the piano keyboard UI."""
    
    def __init__(self):
        """Initialize the piano display component."""
        # Piano dimensions and positioning
        self.white_key_width = 40
        self.white_key_height = 220
        self.black_key_width = 24
        self.black_key_height = 140
        
        self.piano_start_x = 40
        self.piano_start_y = 280
        
        # Key range
        self.first_note = 21  # A0
        self.total_keys = 88  # Full piano range
        
        # Note state tracking
        self.active_notes = defaultdict(lambda: False)
        self.highlighted_notes = defaultdict(lambda: False)
        self.note_velocities = defaultdict(lambda: 127)
        
        # Visual style
        self.white_key_color = (255, 255, 255)
        self.black_key_color = (0, 0, 0)
        self.active_white_color = (180, 180, 255)
        self.active_black_color = (100, 100, 200)
        self.highlight_color = (255, 255, 100)
        self.correct_hit_color = (100, 255, 100)
        
        # Display options
        self.show_note_names = True
        self.show_octave_markers = True
        
        # UI elements
        self.screen = None
        self.font = None
        self.key_font = None
        
        # Key graphics cache
        self.key_rects = {}
    
    def initialize(self, screen, font=None, key_font=None):
        """Initialize the display with pygame screen and fonts.
        
        Args:
            screen: Pygame screen surface
            font: Main font for UI text
            key_font: Font for key labels
        """
        self.screen = screen
        self.font = font or pygame.font.SysFont("Arial", 24)
        self.key_font = key_font or pygame.font.SysFont("Arial", 16)
        
        # Build key rectangles
        self._build_key_rects()
    
    def _build_key_rects(self):
        """Build a cache of key rectangles for drawing and hit detection."""
        self.key_rects = {}
        
        # First pass: calculate white key positions
        white_key_count = 0
        for note in range(self.first_note, self.first_note + self.total_keys):
            if not is_black_key(note):
                x = self.piano_start_x + (white_key_count * self.white_key_width)
                self.key_rects[note] = pygame.Rect(
                    x, self.piano_start_y, 
                    self.white_key_width, self.white_key_height
                )
                white_key_count += 1
        
        # Second pass: calculate black key positions
        for note in range(self.first_note, self.first_note + self.total_keys):
            if is_black_key(note):
                # Find previous white key
                prev_white = note - 1
                while is_black_key(prev_white) and prev_white >= self.first_note:
                    prev_white -= 1
                
                if prev_white in self.key_rects:
                    prev_rect = self.key_rects[prev_white]
                    x = prev_rect.x + self.white_key_width - (self.black_key_width // 2)
                    self.key_rects[note] = pygame.Rect(
                        x, self.piano_start_y, 
                        self.black_key_width, self.black_key_height
                    )
    
    def set_key_range(self, first_note, total_keys):
        """Set the range of piano keys to display.
        
        Args:
            first_note (int): First MIDI note number
            total_keys (int): Total number of keys to display
        """
        self.first_note = first_note
        self.total_keys = total_keys
        self._build_key_rects()
    
    def set_piano_position(self, x, y):
        """Set the position of the piano on screen.
        
        Args:
            x (int): X-coordinate of the piano's left edge
            y (int): Y-coordinate of the piano's top edge
        """
        self.piano_start_x = x
        self.piano_start_y = y
        self._build_key_rects()
    
    def resize(self, width, height):
        """Handle window resize events.
        
        Args:
            width (int): New screen width
            height (int): New screen height
        """
        # Recalculate piano position based on new screen size
        self.piano_start_y = height - self.white_key_height - 20
        self._build_key_rects()
    
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
        """Set a note as highlighted for learning.
        
        Args:
            note (int): MIDI note number
            highlighted (bool): Whether the note is highlighted
        """
        self.highlighted_notes[note] = highlighted
    
    def get_key_at_position(self, x, y):
        """Get the MIDI note number at a screen position.
        
        Args:
            x (int): X-coordinate
            y (int): Y-coordinate
            
        Returns:
            int or None: MIDI note number or None if no key at position
        """
        # Check black keys first (they're on top)
        for note in range(self.first_note, self.first_note + self.total_keys):
            if is_black_key(note) and note in self.key_rects:
                if self.key_rects[note].collidepoint(x, y):
                    return note
        
        # Then check white keys
        for note in range(self.first_note, self.first_note + self.total_keys):
            if not is_black_key(note) and note in self.key_rects:
                if self.key_rects[note].collidepoint(x, y):
                    return note
        
        return None
    
    def get_key_rect(self, note):
        """Get the rectangle for a piano key.
        
        Args:
            note (int): MIDI note number
            
        Returns:
            pygame.Rect or None: Rectangle for the key or None
        """
        return self.key_rects.get(note)
    
    def get_target_line_y(self):
        """Get the y-coordinate for the target line in falling notes mode.
        
        Returns:
            int: Y-coordinate for the target line
        """
        return self.piano_start_y - 50
    
    def draw(self):
        """Draw the piano keyboard and active/highlighted notes."""
        if not self.screen:
            return
        
        # First draw all white keys
        for note in range(self.first_note, self.first_note + self.total_keys):
            if not is_black_key(note) and note in self.key_rects:
                self._draw_key(note)
        
        # Then draw all black keys (so they appear on top)
        for note in range(self.first_note, self.first_note + self.total_keys):
            if is_black_key(note) and note in self.key_rects:
                self._draw_key(note)
        
        # Draw octave markers if enabled
        if self.show_octave_markers:
            self._draw_octave_markers()
    
    def _draw_key(self, note):
        """Draw a single piano key.
        
        Args:
            note (int): MIDI note number
        """
        rect = self.key_rects[note]
        is_black = is_black_key(note)
        
        # Determine key color based on state
        if self.active_notes[note] and self.highlighted_notes[note]:
            # Correct hit (active and highlighted)
            color = self.correct_hit_color
        elif self.active_notes[note]:
            # Just active (being played)
            velocity = self.note_velocities[note]
            brightness = min(255, 100 + int(155 * velocity / 127))
            
            if is_black:
                color = (100, 100, brightness)  # Darker blue for black keys
            else:
                color = (180, 180, brightness)  # Blue for white keys
        elif self.highlighted_notes[note]:
            # Just highlighted (for learning)
            color = self.highlight_color
        else:
            # Default state
            color = self.black_key_color if is_black else self.white_key_color
        
        # Draw key rectangle
        pygame.draw.rect(self.screen, color, rect)
        
        # Draw border
        border_color = (100, 100, 100) if is_black else (0, 0, 0)
        pygame.draw.rect(self.screen, border_color, rect, 1)
        
        # Draw note name if enabled
        if self.show_note_names and self.key_font:
            note_name = get_note_name(note)
            
            # Text color depends on key color
            if self.active_notes[note] or self.highlighted_notes[note]:
                text_color = (0, 0, 0)  # Black text on colored keys
            else:
                text_color = (255, 255, 255) if is_black else (0, 0, 0)
            
            name_text = self.key_font.render(note_name, True, text_color)
            
            # Position text at the bottom of the key
            text_x = rect.x + (rect.width - name_text.get_width()) // 2
            text_y = rect.y + rect.height - name_text.get_height() - 5
            
            self.screen.blit(name_text, (text_x, text_y))
    
    def _draw_octave_markers(self):
        """Draw markers to indicate octaves (C notes)."""
        for note in range(self.first_note, self.first_note + self.total_keys):
            # Check if this is a C note
            if note % 12 == 0 and note in self.key_rects:  # C notes
                rect = self.key_rects[note]
                octave = note // 12 - 1  # Calculate octave number
                
                # Draw a colored marker at the bottom of the key
                marker_height = 5
                marker_rect = pygame.Rect(
                    rect.x, rect.y + rect.height, 
                    rect.width, marker_height
                )
                pygame.draw.rect(self.screen, (200, 200, 200), marker_rect)
                
                # Draw octave number below the marker
                if self.font:
                    text = self.font.render(f"C{octave}", True, (0, 0, 0))
                    self.screen.blit(
                        text, 
                        (rect.x + 2, rect.y + rect.height + marker_height + 2)
                    )
    
    def clear_active_notes(self):
        """Clear all active notes."""
        self.active_notes = defaultdict(lambda: False)
    
    def clear_highlighted_notes(self):
        """Clear all highlighted notes."""
        self.highlighted_notes = defaultdict(lambda: False)
    
    def highlight_chord(self, notes, highlight=True):
        """Highlight a group of notes (chord).
        
        Args:
            notes (List[int]): List of MIDI note numbers
            highlight (bool): Whether to highlight or clear highlight
        """
        for note in notes:
            self.highlighted_notes[note] = highlight
    
    def get_all_key_rects(self):
        """Get a dictionary of all key rectangles.
        
        Returns:
            Dict[int, pygame.Rect]: Dictionary mapping note numbers to rectangles
        """
        return self.key_rects.copy()

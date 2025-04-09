"""
Falling Notes Visualization for the Comprehensive Piano Application
Handles the visualization of notes falling down to the piano keyboard
"""
import pygame
from typing import Dict, List, Tuple, Optional, Any
import logging
from utils.helpers import get_note_name, is_black_key
import random
import math

# Constants for falling notes
FALL_SPEED = 200  # pixels per second
HIT_WINDOW_MS = 200  # milliseconds window for hitting a note
TARGET_LINE_Y_OFFSET = 50  # How far above the piano the target line is

class FallingNote:
    """Represents a note to be played in learning mode."""

    def __init__(
        self,
        note: int,
        start_time_sec: float,
        duration_sec: float,
        target_y: int,
        screen_height: int,
        velocity: int = 127,
        prep_time: float = 3.0
    ):
        """Initialize a falling note.
        
        Args:
            note (int): MIDI note number
            start_time_sec (float): When the note should be played
            duration_sec (float): How long the note should be held
            target_y (int): Y-coordinate of the target line
            screen_height (int): Height of the screen
            velocity (int): MIDI velocity (0-127)
            prep_time (float): Preparation time before the note starts falling
        """
        self.note = note
        self.start_time_sec = start_time_sec
        self.end_time_sec = start_time_sec + duration_sec
        self.duration_sec = max(0.1, duration_sec)  # Ensure minimum height
        self.target_y = target_y
        self.velocity = velocity
        self.prep_time = prep_time
        
        # Height is proportional to duration, with a minimum height
        self.note_height = max(20, self.duration_sec * FALL_SPEED)
        
        # Calculate initial position - notes start above the screen and fall down
        # For debugging, start them visible on screen
        self.start_y = 100  # Start near the top of the screen
        self.current_y = self.start_y
        
        # Note states
        self.active = True          # Whether the note is still active
        self.hit = False            # Whether the note was hit correctly
        self.missed = False         # Whether the note was missed
        self.waiting = False        # Whether the note is waiting at the target line
        self.key_rect = None        # Rectangle of the corresponding piano key
        
        # Performance tracking
        self.hit_time_ms = None     # When the note was actually hit
        self.timing_error_ms = None  # Timing error in milliseconds
        self.accuracy = 0.0         # Accuracy score (0-100%)
        
        # Visual effects
        self.opacity = 255          # Note opacity (for fade effects)
        self.highlight_frames = 0   # Frames to highlight after being hit
        
        # Waiting duration - how long to wait before marking as missed
        self.waiting_duration = 5.0  # 5 seconds to press the key before marking as missed
        self.waiting_time = 0       # Current waiting time
        self.visible = True         # Whether the note is visible on screen
    
    @staticmethod
    def get_note_name(note: int) -> str:
        """Get the standard note name from MIDI note number.
        
        Args:
            note (int): MIDI note number
            
        Returns:
            str: Note name (e.g., "C4", "F#5")
        """
        return get_note_name(note)
    
    def update(self, current_time_sec: float, key_rect_map: Dict[int, pygame.Rect]) -> None:
        """Update the note's vertical position and state.
        
        Args:
            current_time_sec (float): Current playback time
            key_rect_map (Dict): Mapping of note numbers to key rectangles
        """
        # Store the key rectangle for alignment and drawing
        if self.note in key_rect_map:
            self.key_rect = key_rect_map[self.note]
        
        # For debugging - make notes visible and fall slowly
        self.current_y += 2  # Make notes fall at a fixed rate for testing
        
        # Handle note passing target line
        if self.current_y >= self.target_y and not self.hit and not self.missed:
            # Note reached the target line without being hit
            self.waiting = True
            self.waiting_time = current_time_sec
            logging.debug(f"Note {self.note} waiting at y={self.current_y}")
        
        # Update highlight effect
        if self.hit and self.highlight_frames > 0:
            self.highlight_frames -= 1
        
        # Fade out notes after they've been hit or missed
        if self.hit or self.missed:
            self.opacity = max(0, self.opacity - 5)  # Fade out
            
            # Remove completely faded notes
            if self.opacity <= 0:
                self.active = False
                
        # For debugging - remove notes that fall too far
        if self.current_y > self.target_y + 300:
            self.active = False
        
        # Check waiting time
        if self.waiting and current_time_sec - self.waiting_time > self.waiting_duration:
            self.missed = True
            self.waiting = False
            logging.debug(f"Note {self.note} missed after waiting")
    
    def draw(self, screen, colors, font) -> None:
        """Draw the falling note with the label inside.
        
        Args:
            screen: Pygame screen surface
            colors: Dictionary of colors
            font: Pygame font for the note label
        """
        # Don't draw if not active or not visible
        if not self.active or not self.visible:
            return
        
        # If no key_rect, create a fallback rectangle based on note number
        if not self.key_rect:
            # Calculate a basic layout (this is a fallback if the piano key map isn't available)
            # White keys are 23 pixels wide, black keys are 15 pixels wide
            key_width = 15 if is_black_key(self.note) else 23
            # Estimate x position based on the note number (MIDI notes start at 21 for A0)
            approx_x = 30 + ((self.note - 21) * 14)  # Simple approximation
            self.key_rect = pygame.Rect(approx_x, self.target_y, key_width, 10)
            logging.debug(f"Created fallback key_rect for note {self.note} at x={approx_x}")
        
        # Determine color based on state
        if self.hit:
            base_color = colors.get("hit", (100, 255, 100))  # Green for hit notes
        elif self.missed:
            base_color = colors.get("missed", (255, 100, 100))  # Red for missed notes
        elif self.waiting:
            # Pulsating yellow for waiting notes
            pulse_intensity = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() / 200)
            base_color = (
                int(255 * pulse_intensity),  # Pulsating red
                int(255 * pulse_intensity),  # Pulsating green
                50                           # Constant blue
            )
        elif is_black_key(self.note):
            base_color = colors.get("black_note", (100, 100, 160))  # Dark blue for black keys
        else:
            base_color = colors.get("white_note", (100, 160, 255))  # Light blue for white keys
        
        # Apply opacity
        color = (*base_color[:3], self.opacity)
        
        # Draw note rectangle
        note_rect = pygame.Rect(self.key_rect.x, self.current_y - self.note_height, 
                               self.key_rect.width, self.note_height)
        pygame.draw.rect(screen, color, note_rect, border_radius=3)
        
        # Add glowing border for waiting notes
        if self.waiting:
            border_color = (255, 255, 50, self.opacity)  # Bright yellow
            border_width = 2  # Thicker border
        else:
            border_color = (0, 0, 0, self.opacity)
            border_width = 1
            
        pygame.draw.rect(screen, border_color, note_rect, border_width, border_radius=3)
        
        # Debug - draw a marker at the target line
        pygame.draw.rect(screen, (255, 255, 0), 
                        pygame.Rect(self.key_rect.x, self.target_y - 2, self.key_rect.width, 4))
        
        # Draw label if the note is big enough
        if self.note_height > 30:
            note_name = self.get_note_name(self.note)
            label = font.render(note_name, True, (0, 0, 0))
            label_x = self.key_rect.x + (self.key_rect.width - label.get_width()) // 2
            label_y = self.current_y - self.note_height + 5
            screen.blit(label, (label_x, label_y))
        
        # Draw waiting progress bar
        if self.waiting:
            # Calculate how much waiting time has elapsed (as a percentage)
            current_time_sec = pygame.time.get_ticks() / 1000.0
            wait_progress = min(1.0, (current_time_sec - self.waiting_time) / self.waiting_duration)
            
            # Draw background bar
            bar_height = 5
            bar_width = self.key_rect.width
            bar_y = self.target_y + 10
            
            # Background (gray)
            pygame.draw.rect(screen, (80, 80, 80), 
                            pygame.Rect(self.key_rect.x, bar_y, bar_width, bar_height))
            
            # Progress (red to yellow)
            progress_color = (255, int(255 * (1 - wait_progress)), 0)  # Red → Yellow
            pygame.draw.rect(screen, progress_color,
                            pygame.Rect(self.key_rect.x, bar_y, int(bar_width * wait_progress), bar_height))
            
            # Add "Press Now!" text
            press_text = font.render("Press Now!", True, (255, 255, 255))
            screen.blit(press_text, 
                       (self.key_rect.x + self.key_rect.width + 5, self.target_y - font.get_height() // 2))
        
        # Draw hit/miss indicator
        if self.hit and self.timing_error_ms is not None:
            if abs(self.timing_error_ms) < 50:
                text = "Perfect!"
                text_color = (50, 255, 50)
            elif abs(self.timing_error_ms) < 100:
                text = "Good"
                text_color = (180, 255, 50)
            else:
                text = "OK"
                text_color = (255, 255, 50)

            timing_label = font.render(text, True, text_color)
            screen.blit(timing_label, (self.key_rect.x + self.key_rect.width + 5, self.target_y))

    
    def check_hit(self, played_note: int, play_time_ms: int) -> bool:
        """Check if this note was hit correctly.
        
        Args:
            played_note (int): MIDI note that was played
            play_time_ms (int): Time when the note was played
            
        Returns:
            bool: True if the note was hit, False otherwise
        """
        # Already hit or missed
        if self.hit or self.missed or not self.active:
            return False
        
        # Wrong note
        if played_note != self.note:
            return False
        
        # Check timing
        target_time_ms = self.start_time_sec * 1000
        self.timing_error_ms = play_time_ms - target_time_ms
        
        # Within hit window?
        if abs(self.timing_error_ms) <= HIT_WINDOW_MS:
            self.hit = True
            self.hit_time_ms = play_time_ms
            
            # Calculate accuracy based on timing error
            # 100% for perfect timing, down to 0% at the edge of the window
            self.accuracy = 100 * (1 - abs(self.timing_error_ms) / HIT_WINDOW_MS)
            
            # Add highlight effect
            self.highlight_frames = 10
            
            return True
        
        return False


class FallingNotesManager:
    """Manages the creation, updating, and drawing of falling notes."""
    
    def __init__(self, screen_height, target_y):
        """Initialize the falling notes manager.
        
        Args:
            screen_height (int): Height of the screen
            target_y (int): Y-coordinate of the target line
        """
        self.notes = []  # List of active falling notes
        self.screen_height = screen_height
        self.target_y = target_y
        self.prep_time_sec = 3.0  # Time before notes start falling
        
        # Performance metrics
        self.total_notes = 0
        self.hit_notes = 0
        self.missed_notes = 0
        self.accuracy_sum = 0.0
        
        # Visual settings
        self.colors = {
            "target_line": (255, 255, 0),     # Yellow target line
            "white_note": (100, 160, 255),    # Light blue for white key notes
            "black_note": (100, 100, 160),    # Dark blue for black key notes
            "hit": (100, 255, 100),           # Green for hit notes
            "missed": (255, 100, 100),        # Red for missed notes
        }
        
        # Fonts
        self.font = None
        self.screen = None
        self.piano_display = None
        self.visualization_mode = "falling"  # Default visualization mode
    
    def initialize(self, screen, piano_display):
        """Initialize with pygame screen and piano display.
        
        Args:
            screen: Pygame screen surface
            piano_display: Piano display component for key rectangles
        """
        self.screen = screen
        self.piano_display = piano_display
        self.font = pygame.font.SysFont("Arial", 18)
    
    def create_notes_from_midi(self, midi_notes, offset_sec=0.0):
        """Create falling notes from MIDI note data.
        
        Args:
            midi_notes (List): MIDI notes in format [start_time, end_time, note, velocity, track]
            offset_sec (float): Time offset to apply
        """
        self.clear_notes()
        
        # Add prep time to let notes become visible before they need to be played
        offset_sec += self.prep_time_sec
        
        for note_data in midi_notes:
            start_time, end_time, note, velocity, _ = note_data
            
            # Create falling note with adjusted timing
            duration = end_time - start_time
            self.notes.append(
                FallingNote(
                    note=note,
                    start_time_sec=start_time + offset_sec,
                    duration_sec=duration,
                    target_y=self.target_y,
                    screen_height=self.screen_height,
                    velocity=velocity,
                    prep_time=self.prep_time_sec
                )
            )
            
            self.total_notes += 1
    
    def update(self, current_time_sec, key_rect_map):
        """Update all falling notes.
        
        Args:
            current_time_sec (float): Current playback time
            key_rect_map (Dict): Mapping of note numbers to key rectangles
        """
        # Update each note
        for note in self.notes[:]:  # Copy the list to allow removal during iteration
            note.update(current_time_sec, key_rect_map)
            
            # Remove inactive notes
            if not note.active:
                if note.missed and not note.hit:
                    self.missed_notes += 1
                self.notes.remove(note)
    
    def apply_visualization_mode(self, visualization_mode):
        """Apply the visualization mode to all notes.
        
        Args:
            visualization_mode (str): Visualization mode ('falling', 'highlight', or 'both')
        """
        self.visualization_mode = visualization_mode
        
        # Update active notes if needed
        if visualization_mode == "highlight":
            # In highlight-only mode, we still process notes but don't show them visually
            # This makes waiting notes work even without visual falling notes
            for note in self.notes:
                note.visible = False
        else:
            # In other modes, make all notes visible
            for note in self.notes:
                note.visible = True
    
    def get_notes_to_highlight(self, current_time_sec):
        """Get notes that should be highlighted on the keyboard.
        
        Args:
            current_time_sec (float): Current playback time
            
        Returns:
            List[int]: List of MIDI note numbers to highlight
        """
        notes_to_highlight = []
        highlight_window = 0.3  # Highlight notes 300ms before they should be played
        
        for note in self.notes:
            # Highlight notes that are about to be played
            time_to_play = note.start_time_sec - current_time_sec
            if 0 <= time_to_play <= highlight_window:
                notes_to_highlight.append(note.note)
                
        return notes_to_highlight
    
    def draw(self, screen):
        """Draw all falling notes and the target line.
        
        Args:
            screen: Pygame screen surface
        """
        if not self.font:
            return
            
        # Draw target line
        pygame.draw.line(
            screen,
            self.colors["target_line"],
            (0, self.target_y),
            (screen.get_width(), self.target_y),
            2
        )
        
        # Draw falling notes
        for note in self.notes:
            note.draw(screen, self.colors, self.font)
    
    def check_note_hit(self, note, play_time_ms=None):
        """Check if a played note hits any falling notes.
        
        Args:
            note (int): MIDI note number that was played
            play_time_ms (int, optional): Time when the note was played. 
                                         If None, current time will be used.
            
        Returns:
            dict: Hit information with keys:
                 - hit: True if note was hit
                 - timing_error_ms: Timing error in milliseconds (if hit)
        """
        # Use current time if play_time_ms is not provided
        if play_time_ms is None:
            play_time_ms = pygame.time.get_ticks()
        
        # Check each falling note for a hit
        for falling_note in self.notes:
            if falling_note.note == note and falling_note.active and not falling_note.hit:
                # Calculate timing error
                timing_error_ms = abs(play_time_ms - falling_note.start_time_sec * 1000)
                
                # Mark as hit if within acceptable timing window
                if timing_error_ms <= HIT_WINDOW_MS:
                    falling_note.hit = True
                    self.hit_notes += 1
                    
                    # Update accuracy and average timing error
                    accuracy = max(0, 1.0 - (timing_error_ms / HIT_WINDOW_MS))
                    falling_note.accuracy = accuracy
                    self.accuracy_sum += accuracy
                    
                    return {
                        'hit': True,
                        'timing_error_ms': timing_error_ms
                    }
        
        # No hit found
        return {
            'hit': False,
            'timing_error_ms': 0
        }

    def get_performance_stats(self):
        """Get current performance statistics.
        
        Returns:
            Dict: Performance statistics
        """
        accuracy = self.accuracy_sum / self.hit_notes if self.hit_notes > 0 else 0
        return {
            "total_notes": self.total_notes,
            "hit_notes": self.hit_notes,
            "missed_notes": self.missed_notes,
            "accuracy": accuracy,
            "completion": (self.hit_notes + self.missed_notes) / max(1, self.total_notes) * 100
        }
    
    def clear_notes(self):
        """Clear all notes and reset statistics."""
        self.notes = []
        self.total_notes = 0
        self.hit_notes = 0
        self.missed_notes = 0
        self.accuracy_sum = 0.0
    
    def reset(self):
        """Reset the falling notes manager by clearing all active notes."""
        self.notes = []
        self.total_notes = 0
        self.hit_notes = 0
        self.missed_notes = 0
        self.accuracy_sum = 0.0
        logging.info("FallingNotesManager reset")
    
    def resize(self, screen_height, target_y):
        """Handle screen resize.
        
        Args:
            screen_height (int): New screen height
            target_y (int): New target line Y-coordinate
        """
        self.screen_height = screen_height
        self.target_y = target_y

    def add_note(self, note, duration_ms, from_learning_track=True):
        """Add a falling note to be displayed.
        
        Args:
            note (int): MIDI note number
            duration_ms (float): Note duration in milliseconds
            from_learning_track (bool): Whether this note is from the learning track
        """
        # Calculate when the note should be played (current time + prep time)
        current_time_sec = pygame.time.get_ticks() / 1000.0
        start_time_sec = current_time_sec + self.prep_time_sec
        duration_sec = duration_ms / 1000.0  # Convert ms to seconds
        
        # Create and add the falling note
        self.notes.append(
            FallingNote(
                note=note,
                start_time_sec=start_time_sec,
                duration_sec=duration_sec,
                target_y=self.target_y,
                screen_height=self.screen_height,
                velocity=100,  # Default velocity
                prep_time=self.prep_time_sec
            )
        )
        
        self.total_notes += 1
        logging.debug(f"Added falling note: {note}, start: {start_time_sec}, duration: {duration_sec}s")

    def handle_note_input(self, note, velocity=127):
        """Handle user input for a note.
        
        Args:
            note (int): MIDI note number that was pressed
            velocity (int, optional): MIDI velocity. Defaults to 127.
            
        Returns:
            bool: True if the note was waiting and is now hit, False otherwise
        """
        current_time_sec = pygame.time.get_ticks() / 1000.0
        
        # Check for waiting notes
        for falling_note in self.notes:
            if falling_note.note == note and falling_note.waiting and not falling_note.hit:
                # Mark the note as hit
                falling_note.hit = True
                falling_note.waiting = False
                falling_note.hit_time_ms = current_time_sec * 1000
                
                # Calculate timing accuracy
                # 100% for perfect timing, down to 0% at the edge of the window
                target_time_ms = falling_note.start_time_sec * 1000
                falling_note.timing_error_ms = falling_note.hit_time_ms - target_time_ms
                
                # Set highlight effect
                falling_note.highlight_frames = 10
                
                logging.debug(f"Note {note} hit while waiting, timing error: {falling_note.timing_error_ms:.1f}ms")
                return True
                
        return False

"""
UI Manager for the Comprehensive Piano Application
Coordinates all UI components and handles mode switching
"""
import pygame
import os
from typing import Dict, List, Tuple, Optional, Any, Callable

from modules.ui.piano_display import PianoDisplay
from modules.ui.falling_notes import FallingNotesManager
from modules.ui.performance_metrics import PerformanceMetrics
from modules.ui.settings import SettingsUI

class UIManager:
    """Manages all UI components for the comprehensive piano application."""
    
    def __init__(self):
        """Initialize the UI manager."""
        # Pygame setup
        pygame.init()
        pygame.font.init()
        self.screen = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Default window size
        self.width = 1600
        self.height = 800
        
        # UI components
        self.piano_display = PianoDisplay()
        # Initialize falling notes manager with temporary values
        # These will be properly set in the initialize method
        self.falling_notes_manager = None
        self.performance_metrics = PerformanceMetrics()
        self.settings_ui = SettingsUI()
        
        # Application state
        self.current_mode = "free_play"  # free_play, learning, settings
        self.paused = False
        
        # Fonts
        self.font = None
        self.title_font = None
        self.small_font = None
        
        # UI elements
        self.buttons = {}
        self.pop_up_message = None
        self.pop_up_timer = 0
        
        # FPS counter
        self.show_fps = False
        self.fps_count = 0
        self.last_fps_update = 0
        
        # Reference to main application
        self.app = None
    
    def initialize(self, width=1600, height=800, fullscreen=False, app=None):
        """Initialize the UI system and pygame display.
        
        Args:
            width (int): Window width
            height (int): Window height
            fullscreen (bool): Whether to start in fullscreen mode
            app (object): Reference to main application
        """
        self.width = width
        self.height = height
        self.app = app  # Store reference to main application
        
        # Set up display
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.width, self.height = self.screen.get_size()
        else:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        pygame.display.set_caption("Comprehensive Piano")
        
        # Initialize fonts
        self.font = pygame.font.SysFont("Arial", 24)
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Get target line Y position from piano display
        self.piano_display.initialize(self.screen, self.small_font, self.small_font)
        target_y = self.piano_display.get_target_line_y()
        
        # Now initialize the falling notes manager with proper values
        self.falling_notes_manager = FallingNotesManager(self.height, target_y)
        self.falling_notes_manager.initialize(self.screen, self.piano_display)
        
        self.performance_metrics.initialize(self.screen, self.small_font, self.font, self.title_font)
        self.settings_ui.initialize(self.screen, self.font, self.title_font)
        
        # Set up settings callback
        self.settings_ui.set_settings_changed_callback(self._apply_settings)
        
        # Apply initial settings
        self._apply_settings()
        
        # Create UI buttons
        self._create_buttons()
        
        # Set running state
        self.running = True
    
    def _create_buttons(self):
        """Create UI buttons for mode switching and controls."""
        # Button dimensions
        button_width = 150
        button_height = 40
        margin = 10
        
        # Top-left menu buttons
        self.buttons = {
            "free_play": {
                "rect": pygame.Rect(margin, margin, button_width, button_height),
                "text": "Free Play",
                "action": lambda: self.set_mode("free_play")
            },
            "learning": {
                "rect": pygame.Rect(margin*2 + button_width, margin, button_width, button_height),
                "text": "Learning Mode",
                "action": lambda: self.set_mode("learning")
            },
            "settings": {
                "rect": pygame.Rect(margin*3 + button_width*2, margin, button_width, button_height),
                "text": "Settings",
                "action": self.show_settings
            }
        }
        
        # Learning mode controls (only visible in learning mode)
        learning_button_y = self.height - button_height - margin
        self.buttons.update({
            "start_learning": {
                "rect": pygame.Rect(margin, learning_button_y, button_width, button_height),
                "text": "Start",
                "action": self._start_learning_session,
                "visible_in": ["learning"]
            },
            "pause_learning": {
                "rect": pygame.Rect(margin*2 + button_width, learning_button_y, button_width, button_height),
                "text": "Pause",
                "action": self._toggle_pause,
                "visible_in": ["learning"]
            },
            "reset_learning": {
                "rect": pygame.Rect(margin*3 + button_width*2, learning_button_y, button_width, button_height),
                "text": "Reset",
                "action": self._reset_learning_session,
                "visible_in": ["learning"]
            },
            "load_midi": {
                "rect": pygame.Rect(margin*4 + button_width*3, learning_button_y, button_width, button_height),
                "text": "Load MIDI",
                "action": self._load_midi_file,
                "visible_in": ["learning", "free_play"]
            }
        })
    
    def _load_midi_file(self):
        """Open a dialog to load a MIDI file."""
        # Store the current directory to reset afterwards
        current_dir = os.getcwd()
        
        # Show popup message
        self.show_popup("Select a MIDI file to load", 1000)
        
        try:
            # Create a temporary directory browser (simple text-based)
            midi_dir = os.path.join(current_dir, "midi")
            
            # Create midi directory if it doesn't exist
            if not os.path.exists(midi_dir):
                os.makedirs(midi_dir)
                self.show_popup(f"Created MIDI directory at {midi_dir}", 2000)
                
            # Get list of MIDI files
            midi_files = [f for f in os.listdir(midi_dir) if f.lower().endswith(('.mid', '.midi'))]
            
            if not midi_files:
                self.show_popup("No MIDI files found in the 'midi' directory", 3000)
                return
                
            # Create a selection menu
            selection_height = len(midi_files) * 30 + 60  # Height based on number of files
            selection_width = 500
            selection_x = (self.width - selection_width) // 2
            selection_y = (self.height - selection_height) // 2
            
            # Create selection surface
            selection_surface = pygame.Surface((selection_width, selection_height))
            selection_surface.fill((240, 240, 240))
            
            # Draw title
            title_text = self.title_font.render("Select a MIDI file", True, (0, 0, 0))
            selection_surface.blit(
                title_text, 
                ((selection_width - title_text.get_width()) // 2, 10)
            )
            
            # Draw file options
            file_rects = []
            for i, file_name in enumerate(midi_files):
                file_rect = pygame.Rect(20, 50 + i*30, selection_width - 40, 25)
                file_rects.append((file_rect, file_name))
                
                # Draw file option
                pygame.draw.rect(selection_surface, (220, 220, 220), file_rect)
                pygame.draw.rect(selection_surface, (0, 0, 0), file_rect, 1)
                
                file_text = self.font.render(file_name, True, (0, 0, 0))
                selection_surface.blit(file_text, (file_rect.x + 10, file_rect.y + 2))
            
            # Show the selection screen and wait for a choice
            selected_file = None
            selection_active = True
            
            while selection_active and self.running:
                # Process events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        selection_active = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            selection_active = False
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        # Adjust for the selection window position
                        rel_pos = (mouse_pos[0] - selection_x, mouse_pos[1] - selection_y)
                        
                        # Check if click is on a file
                        for rect, file_name in file_rects:
                            if rect.collidepoint(rel_pos):
                                selected_file = file_name
                                selection_active = False
                                break
                
                # Draw the current screen
                self.screen.fill((240, 240, 250))
                self.piano_display.draw()
                self._draw_buttons()
                
                # Draw selection screen on top
                self.screen.blit(selection_surface, (selection_x, selection_y))
                
                # Update display
                pygame.display.flip()
                self.clock.tick(60)
            
            # Load the selected file if one was chosen
            if selected_file:
                midi_path = os.path.join(midi_dir, selected_file)
                if self.app and hasattr(self.app, 'load_midi_file'):
                    if self.app.load_midi_file(midi_path):
                        self.show_popup(f"Loaded MIDI file: {selected_file}", 2000)
                        
                        # Prepare for learning mode
                        if self.current_mode == "learning" and hasattr(self.app, '_prepare_learning_track'):
                            self.app._prepare_learning_track()
                            self.show_popup("Learning track prepared", 1000)
                    else:
                        self.show_popup(f"Error loading MIDI file", 2000)
                else:
                    self.show_popup("MIDI loading not supported", 2000)
            
        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            self.show_popup(f"Error: {str(e)}", 3000)
            
    def _apply_settings(self):
        """Apply settings to UI components."""
        settings = self.settings_ui.settings
        
        # Apply piano display settings
        self.piano_display.show_note_names = settings["show_note_names"]
        self.piano_display.show_octave_markers = settings["show_octave_markers"]
        self.piano_display.set_key_range(
            settings["key_range"]["first_note"],
            settings["key_range"]["total_keys"]
        )
        
        # Apply falling notes settings
        self.falling_notes_manager.falling_speed = settings["falling_speed"]
        self.falling_notes_manager.hit_window_ms = settings["hit_window"]
        
        # Apply performance metrics settings
        if settings["show_performance_stats"]:
            self.performance_metrics.show()
        else:
            self.performance_metrics.hide()
            
    def show_settings(self):
        """Show the settings UI."""
        self.settings_ui.show()
        
    def resize(self, width, height):
        """Handle window resize events.
        
        Args:
            width (int): New window width
            height (int): New window height
        """
        self.width = width
        self.height = height
        
        # Update component positions
        self.piano_display.resize(width, height)
        
        # Get updated target line Y position
        target_y = self.piano_display.get_target_line_y()
        
        # Update the falling notes manager with new dimensions
        self.falling_notes_manager.resize(height, target_y)
        
        self.performance_metrics.resize(width, height)
        
        # Update button positions
        self._create_buttons()
        
    def set_mode(self, mode):
        """Switch between application modes.
        
        Args:
            mode (str): Application mode (free_play, learning, settings)
        """
        if mode == self.current_mode:
            return
            
        self.current_mode = mode
        
        # Reset state based on mode
        if mode == "free_play":
            self.falling_notes_manager.clear_notes()
            self.performance_metrics.hide()
            
        elif mode == "learning":
            self.falling_notes_manager.clear_notes()
            self.performance_metrics.reset_metrics()
            if self.settings_ui.get_setting("show_performance_stats"):
                self.performance_metrics.show()
                
        self.paused = False
        
    def handle_event(self, event):
        """Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            bool: True if the event was handled and should not be propagated
        """
        # First check if settings UI is active
        if self.settings_ui.is_visible():
            if self.settings_ui.handle_event(event):
                return True
        
        # Window resize
        if event.type == pygame.VIDEORESIZE:
            self.resize(event.w, event.h)
            return True
            
        # Mouse click
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check buttons
            for button_key, button in self.buttons.items():
                # Skip buttons not visible in current mode
                if "visible_in" in button and self.current_mode not in button["visible_in"]:
                    continue
                    
                if button["rect"].collidepoint(event.pos):
                    button["action"]()
                    return True
            
            # Check piano keys
            note = self.piano_display.get_key_at_position(event.pos[0], event.pos[1])
            if note is not None:
                # Call the note_on event for external handlers
                return False  # Let the input handler process this
                
        # Debug key - toggle FPS display
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.show_fps = not self.show_fps
            return True
            
        return False
        
    def _start_learning_session(self):
        """Start a learning session."""
        if self.current_mode != "learning":
            self.set_mode("learning")
            
        self.performance_metrics.reset_metrics()
        self.falling_notes_manager.reset()
        self.paused = False
        
        # Show temporary message
        self.show_popup("Learning session started")
    
    def _toggle_pause(self):
        """Toggle pause state in learning mode."""
        if self.current_mode != "learning":
            return
            
        self.paused = not self.paused
        
        # Update button text
        self.buttons["pause_learning"]["text"] = "Resume" if self.paused else "Pause"
        
        # Show temporary message
        self.show_popup("Paused" if self.paused else "Resumed")
    
    def _reset_learning_session(self):
        """Reset the learning session."""
        if self.current_mode != "learning":
            return
            
        self.performance_metrics.reset_metrics()
        self.falling_notes_manager.reset()
        self.paused = False
        
        # Update button text
        self.buttons["pause_learning"]["text"] = "Pause"
        
        # Show temporary message
        self.show_popup("Learning session reset")
        
    def show_popup(self, message, duration=1500):
        """Show a temporary pop-up message.
        
        Args:
            message (str): Message to display
            duration (int): Duration in milliseconds
        """
        self.pop_up_message = message
        self.pop_up_timer = duration
        
    def draw(self, delta_time):
        """Draw all UI components.
        
        Args:
            delta_time (float): Time since last frame in seconds
        """
        if not self.screen:
            return
            
        # Clear screen
        self.screen.fill((240, 240, 250))
        
        # Draw piano
        self.piano_display.draw()
        
        # Draw mode-specific components
        if self.current_mode == "learning" and not self.paused:
            # Get the key rect map from piano display for falling notes positioning
            key_rect_map = self.piano_display.get_all_key_rects()
            self.falling_notes_manager.update(delta_time, key_rect_map)
        
        if self.current_mode == "learning":
            self.falling_notes_manager.draw(self.screen)
            
            # Draw target line
            target_y = self.piano_display.get_target_line_y()
            pygame.draw.line(
                self.screen,
                (255, 100, 100),
                (0, target_y),
                (self.width, target_y),
                2
            )
        
        # Draw performance metrics if enabled and in learning mode
        if self.current_mode == "learning" and self.settings_ui.get_setting("show_performance_stats"):
            self.performance_metrics.draw()
        
        # Draw UI buttons
        self._draw_buttons()
        
        # Draw popup message if active
        if self.pop_up_message:
            self._draw_popup()
            self.pop_up_timer -= delta_time * 1000
            if self.pop_up_timer <= 0:
                self.pop_up_message = None
        
        # Draw settings UI on top if active
        if self.settings_ui.is_visible():
            self.settings_ui.draw()
        
        # Draw FPS counter if enabled
        if self.show_fps:
            self._draw_fps()
        
        # Update display
        pygame.display.flip()
        
    def _draw_buttons(self):
        """Draw UI buttons."""
        for button_key, button in self.buttons.items():
            # Skip buttons not visible in current mode
            if "visible_in" in button and self.current_mode not in button["visible_in"]:
                continue
                
            # Highlight active mode button
            if button_key == self.current_mode:
                color = (100, 100, 250)
            else:
                color = (100, 100, 200)
                
            # Draw button
            pygame.draw.rect(self.screen, color, button["rect"])
            pygame.draw.rect(self.screen, (0, 0, 0), button["rect"], 1)
            
            # Draw button text
            text = self.font.render(button["text"], True, (255, 255, 255))
            self.screen.blit(
                text,
                (
                    button["rect"].x + (button["rect"].width - text.get_width()) // 2,
                    button["rect"].y + (button["rect"].height - text.get_height()) // 2
                )
            )
            
    def _draw_popup(self):
        """Draw the popup message."""
        if not self.pop_up_message:
            return
            
        # Fade out based on remaining time
        alpha = min(255, int(self.pop_up_timer * 1.7))
        
        # Create text surface
        text = self.font.render(self.pop_up_message, True, (0, 0, 0))
        
        # Create background with padding
        padding = 20
        popup_rect = pygame.Rect(
            (self.width - text.get_width()) // 2 - padding,
            self.height // 4 - padding,
            text.get_width() + padding * 2,
            text.get_height() + padding * 2
        )
        
        # Create surfaces with alpha
        background = pygame.Surface((popup_rect.width, popup_rect.height), pygame.SRCALPHA)
        background.fill((255, 255, 255, alpha))
        
        # Draw to screen
        self.screen.blit(background, popup_rect.topleft)
        
        # Draw border
        pygame.draw.rect(
            self.screen,
            (0, 0, 0, alpha),
            popup_rect,
            2
        )
        
        # Apply alpha to text
        text.set_alpha(alpha)
        
        # Draw text
        self.screen.blit(
            text,
            (
                (self.width - text.get_width()) // 2,
                self.height // 4
            )
        )
        
    def _draw_fps(self):
        """Draw the FPS counter."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fps_update > 500:  # Update every 500ms
            self.fps_count = int(self.clock.get_fps())
            self.last_fps_update = current_time
        
        fps_text = self.font.render(f"FPS: {self.fps_count}", True, (0, 0, 0))
        self.screen.blit(fps_text, (self.width - fps_text.get_width() - 10, 10))
        
    def update_piano_key(self, note, active=True, velocity=127):
        """Update the state of a piano key.
        
        Args:
            note (int): MIDI note number
            active (bool): Whether the note is active
            velocity (int): MIDI velocity (0-127)
        """
        self.piano_display.set_note_active(note, active, velocity)
        
    def update_highlighted_notes(self, notes=None, clear=False):
        """Update highlighted notes on the piano.
        
        Args:
            notes (List[int], optional): List of notes to highlight
            clear (bool): Whether to clear all highlights
        """
        if clear:
            self.piano_display.clear_highlighted_notes()
        elif notes:
            for note in notes:
                self.piano_display.set_note_highlighted(note, True)
                
    def add_falling_note(self, note, duration_ms, from_learning_track=True):
        """Add a falling note.
        
        Args:
            note (int): MIDI note number
            duration_ms (float): Note duration in milliseconds
            from_learning_track (bool): Whether this note is from the learning track
        """
        if self.current_mode == "learning":
            self.falling_notes_manager.add_note(note, duration_ms, from_learning_track)
            
    def register_note_hit(self, note, timing_error_ms):
        """Register a successful note hit in learning mode.
        
        Args:
            note (int): MIDI note number
            timing_error_ms (float): Timing error in milliseconds
        """
        if self.current_mode == "learning":
            self.performance_metrics.note_hit(abs(timing_error_ms))
            self.piano_display.set_note_highlighted(note, True)
            
    def register_note_miss(self, note=None):
        """Register a missed note in learning mode.
        
        Args:
            note (int, optional): MIDI note number that was missed
        """
        if self.current_mode == "learning":
            self.performance_metrics.note_missed()
            
    def is_paused(self):
        """Check if the application is paused.
        
        Returns:
            bool: True if paused
        """
        return self.paused
        
    def is_learning_mode(self):
        """Check if the application is in learning mode.
        
        Returns:
            bool: True if in learning mode
        """
        return self.current_mode == "learning"
        
    def get_target_line_y(self):
        """Get the y-coordinate of the target line.
        
        Returns:
            int: Y-coordinate
        """
        return self.piano_display.get_target_line_y()
        
    def main_loop(self):
        """Run the main UI loop."""
        self.running = True
        
        while self.running:
            # Calculate delta time
            delta_time = self.clock.tick(60) / 1000.0
            
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                    
                # Skip other events if we handled it
                if self.handle_event(event):
                    continue
                
                # Add additional event handling here
            
            # Draw UI
            self.draw(delta_time)
        
        # Clean up
        pygame.quit()
        
    def quit(self):
        """Quit the application."""
        self.running = False

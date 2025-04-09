"""
Comprehensive Piano Application
Main entry point for the integrated piano visualization, learning, and playing application

This application combines multiple piano-related functionality including:
- Piano visualization 
- MIDI file parsing and playback
- Audio engine with sample-based and synthesized sound
- Learning mode with falling notes visualization
- Performance metrics
- Input handling from keyboard and MIDI devices
"""
import os
import sys
import time
import pygame
import pygame.midi
import argparse
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to show all log messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Import application modules
from modules.audio_engine import AudioEngine
from modules.input_handler import InputHandler
from modules.midi_parser import MIDIParser
from modules.music_theory import MusicTheory
from modules.ui.ui_manager import UIManager
from modules.ui.falling_notes import FallingNotesManager
from utils.helpers import get_note_name, is_black_key, midi_to_freq

class ComprehensivePiano:
    """Main application class for the Comprehensive Piano."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize components
        self.ui_manager = UIManager()
        self.audio_engine = AudioEngine()
        self.input_handler = InputHandler()
        self.midi_parser = MIDIParser()
        self.music_theory = MusicTheory()
        
        # Application state
        self.current_midi_file = None
        self.current_midi_data = None
        self.playback_started = False
        self.playback_start_time = 0
        self.elapsed_time = 0
        self.active_notes = set()
        
        # Learning mode
        self.learning_track_notes = []
        self.learning_track_index = 0
        self.next_learning_note_time = 0
        
        # MIDI device
        self.midi_input_device = None
    
    def initialize(self):
        """Initialize all application components."""
        print("Initializing Comprehensive Piano application...")
        
        # Initialize UI
        self.ui_manager.initialize(width=1600, height=800, app=self)
        
        # Initialize audio engine
        self.audio_engine.initialize()
        
        # Set up audio callbacks
        def note_on_callback(note, velocity):
            self.ui_manager.update_piano_key(note, True, velocity)
            
        def note_off_callback(note):
            self.ui_manager.update_piano_key(note, False)
            
        self.audio_engine.set_note_callbacks(note_on_callback, note_off_callback)
        
        # Initialize input handler
        self.input_handler.initialize()
        
        # Set up input callbacks
        def key_on_callback(note, velocity):
            self._handle_note_on(note, velocity)
            
        def key_off_callback(note):
            self._handle_note_off(note)
            
        self.input_handler.set_note_callbacks(key_on_callback, key_off_callback)
        
        print("Initialization complete")
    
    def _handle_note_on(self, note, velocity=127):
        """Handle note-on event from input.
        
        Args:
            note (int): MIDI note number
            velocity (int): Note velocity (0-127)
        """
        # Update UI
        self.ui_manager.update_piano_key(note, True, velocity)
        
        # Play audio
        self.audio_engine.play_note(note, velocity)
        
        # Add to active notes
        self.active_notes.add(note)
        
        # Check for note hit in learning mode
        if self.ui_manager.is_learning_mode() and not self.ui_manager.is_paused():
            # First check for waiting notes that need to be hit
            note_hit = self.ui_manager.falling_notes_manager.handle_note_input(note, velocity)
            
            # If no waiting notes matched, check for normal note hits
            if not note_hit:
                hit_info = self.ui_manager.falling_notes_manager.check_note_hit(note)
                if hit_info['hit']:
                    self.ui_manager.register_note_hit(note, hit_info['timing_error_ms'])
    
    def _handle_note_off(self, note):
        """Handle note-off event from input.
        
        Args:
            note (int): MIDI note number
        """
        # Update UI
        self.ui_manager.update_piano_key(note, False)
        
        # Stop audio
        self.audio_engine.stop_note(note)
        
        # Remove from active notes
        if note in self.active_notes:
            self.active_notes.remove(note)
    
    def load_midi_file(self, file_path):
        """Load a MIDI file for playback or learning.
        
        Args:
            file_path (str): Path to MIDI file
            
        Returns:
            bool: True if file loaded successfully
        """
        if not os.path.exists(file_path):
            print(f"Error: MIDI file not found: {file_path}")
            return False
            
        try:
            # Parse the MIDI file
            self.current_midi_data = self.midi_parser.parse_midi_file(file_path)
            self.current_midi_file = file_path
            
            # Reset playback state
            self.playback_started = False
            self.elapsed_time = 0
            
            # Reset learning mode if active
            if self.ui_manager.is_learning_mode():
                self._prepare_learning_track()
                self.ui_manager.falling_notes_manager.clear_notes()
                logging.info(f"Prepared learning track with {len(self.learning_track_notes)} notes")
                
            # Make sure we're in learning mode after loading a MIDI file
            if not self.ui_manager.is_learning_mode():
                self.ui_manager.toggle_learning_mode()
                logging.info("Automatically switched to learning mode after loading MIDI file")
                
            print(f"Loaded MIDI file: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"Error loading MIDI file: {e}")
            return False
    
    def _prepare_learning_track(self):
        """Prepare the learning track from loaded MIDI data."""
        if not self.current_midi_data:
            return
            
        # Extract notes from parsed MIDI data
        notes = []
        
        # The parsed MIDI data has 'notes' as a flat list in format:
        # [start_time, end_time, note, velocity, track_idx]
        if 'notes' in self.current_midi_data:
            for note_data in self.current_midi_data['notes']:
                start_time, end_time, note_number, velocity, track_idx = note_data
                
                # Convert times from seconds to milliseconds for consistent timing
                start_time_ms = start_time * 1000
                end_time_ms = end_time * 1000
                
                notes.append({
                    'note': note_number,
                    'start_time': start_time_ms,
                    'end_time': end_time_ms,
                    'velocity': velocity,
                    'duration': end_time_ms - start_time_ms
                })
                
            # Debug log
            logging.debug(f"Prepared {len(notes)} notes for learning track")
        else:
            logging.warning("No notes found in MIDI data for learning track")
            
        # Sort notes by start time
        self.learning_track_notes = sorted(notes, key=lambda x: x['start_time'])
        self.learning_track_index = 0
        self.next_learning_note_time = 0
    
    def _update_learning_mode(self, delta_time):
        """Update learning mode state.
        
        Args:
            delta_time (float): Time since last frame in seconds
        """
        if not self.ui_manager.is_learning_mode() or self.ui_manager.is_paused():
            return
            
        if not self.learning_track_notes:
            if self.current_midi_file:
                self._prepare_learning_track()
                logging.info(f"Preparing learning track from MIDI file: {os.path.basename(self.current_midi_file)}")
            return
            
        # Update elapsed time
        self.elapsed_time += delta_time * 1000  # Convert to ms
        
        # Add new falling notes as needed
        while (self.learning_track_index < len(self.learning_track_notes) and 
               self.learning_track_notes[self.learning_track_index]['start_time'] <= 
               self.elapsed_time + 3000):  # Add notes that will appear in the next 3 seconds
            
            note_data = self.learning_track_notes[self.learning_track_index]
            note = note_data['note']
            duration = note_data['duration']
            
            # Calculate when the note should hit the target line
            target_time = note_data['start_time']
            
            # Only add if it's in the future
            if target_time > self.elapsed_time:
                self.ui_manager.add_falling_note(note, duration, True)
                logging.debug(f"Added learning note: {note}, duration: {duration}ms")
            
            self.learning_track_index += 1
    
    def _handle_key_press(self, key):
        """Handle special key presses.
        
        Args:
            key: Pygame key constant
        """
        # Handle special keys
        if key == pygame.K_ESCAPE:
            # ESC: Toggle settings panel
            if self.ui_manager.settings_ui.is_visible():
                self.ui_manager.settings_ui.hide()
            else:
                self.ui_manager.settings_ui.show()
                
        elif key == pygame.K_SPACE:
            # Space: Toggle pause in learning mode
            if self.ui_manager.is_learning_mode():
                self.ui_manager.toggle_pause()
                
        # Visualization mode shortcuts in learning mode
        elif self.ui_manager.is_learning_mode():
            if key == pygame.K_1:
                # 1: Switch to falling notes only
                self.ui_manager.settings_ui.set_setting("learning_visualization", "falling")
                self.ui_manager.show_popup("Switched to Falling Notes Only")
                
            elif key == pygame.K_2:
                # 2: Switch to highlighted keys only
                self.ui_manager.settings_ui.set_setting("learning_visualization", "highlight")
                self.ui_manager.show_popup("Switched to Highlighted Keys Only")
                
            elif key == pygame.K_3:
                # 3: Switch to both visualization modes
                self.ui_manager.settings_ui.set_setting("learning_visualization", "both")
                self.ui_manager.show_popup("Switched to Combined Mode (Notes + Highlights)")
    
    def run(self):
        """Run the application main loop."""
        print("Running Comprehensive Piano application...")
        
        try:
            # Initial setup
            last_time = time.time()
            
            # Run UI manager's main loop
            while self.ui_manager.running:
                # Calculate delta time
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time
                
                # Get all events
                events = pygame.event.get()
                
                # Check for quit event
                for event in events:
                    if event.type == pygame.QUIT:
                        self.ui_manager.running = False
                        break
                
                # Process input with the retrieved events
                self.input_handler.process_keyboard_events(events)
                self.input_handler.process_midi_input()
                
                # Update learning mode
                self._update_learning_mode(delta_time)
                
                # Handle key presses
                for event in events:
                    if event.type == pygame.KEYDOWN:
                        self._handle_key_press(event.key)
                
                # Let UI manager handle events
                for event in events:
                    # Skip if UI handled it
                    if self.ui_manager.handle_event(event):
                        continue
                
                # Draw UI
                self.ui_manager.draw(delta_time)
                
                # Control frame rate
                self.ui_manager.clock.tick(60)
                
        except KeyboardInterrupt:
            print("Application interrupted by user")
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            self._cleanup()

    def _cleanup(self):
        """Clean up resources before exit."""
        print("Cleaning up resources...")
        
        # Close audio engine
        self.audio_engine.cleanup()
        
        # Close MIDI input
        self.input_handler.cleanup()
        
        # Quit pygame
        pygame.quit()
        
        print("Application closed")

def parse_arguments():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Comprehensive Piano Application")
    parser.add_argument("--midi", "-m", help="Path to MIDI file to load on startup")
    parser.add_argument("--fullscreen", "-f", action="store_true", help="Start in fullscreen mode")
    parser.add_argument("--learning", "-l", action="store_true", help="Start in learning mode")
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create and initialize the application
    app = ComprehensivePiano()
    app.initialize()
    
    # Load MIDI file if specified
    if args.midi:
        app.load_midi_file(args.midi)
    
    # Set mode if specified
    if args.learning:
        app.ui_manager.set_mode("learning")
    
    # Run the application
    app.run()

if __name__ == "__main__":
    main()

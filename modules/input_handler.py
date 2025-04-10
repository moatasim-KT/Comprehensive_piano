"""
Input Handler module for the Comprehensive Piano Application
Handles keyboard and MIDI input devices
"""
import pygame
import pygame.midi
import logging
from typing import Dict, List, Tuple, Callable, Any, Optional
import time

class InputHandler:
    """Handles all user input including computer keyboard and MIDI devices."""
    
    def __init__(self):
        """Initialize the input handler."""
        self.midi_input = None
        self.midi_input_id = None
        self.midi_devices = []
        
        # Keyboard mapping (computer keyboard to MIDI notes)
        self.key_mapping = {
            # Lower octave
            pygame.K_z: 36,  # C2
            pygame.K_s: 37,  # C#2
            pygame.K_x: 38,  # D2
            pygame.K_d: 39,  # D#2
            pygame.K_c: 40,  # E2
            pygame.K_v: 41,  # F2
            pygame.K_g: 42,  # F#2
            pygame.K_b: 43,  # G2
            pygame.K_h: 44,  # G#2
            pygame.K_n: 45,  # A2
            pygame.K_j: 46,  # A#2
            pygame.K_m: 47,  # B2
            
            # Middle octave
            pygame.K_q: 48,  # C3
            pygame.K_2: 49,  # C#3
            pygame.K_w: 50,  # D3
            pygame.K_3: 51,  # D#3
            pygame.K_e: 52,  # E3
            pygame.K_r: 53,  # F3
            pygame.K_5: 54,  # F#3
            pygame.K_t: 55,  # G3
            pygame.K_6: 56,  # G#3
            pygame.K_y: 57,  # A3
            pygame.K_7: 58,  # A#3
            pygame.K_u: 59,  # B3
            
            # Upper octave
            pygame.K_i: 60,  # C4 (middle C)
            pygame.K_9: 61,  # C#4
            pygame.K_o: 62,  # D4
            pygame.K_0: 63,  # D#4
            pygame.K_p: 64,  # E4
            pygame.K_LEFTBRACKET: 65,  # F4
            pygame.K_EQUALS: 66,  # F#4
            pygame.K_RIGHTBRACKET: 67,  # G4
        }
        
        # Track currently pressed keys to avoid repeat events
        self.pressed_keys = set()
        
        # Callback functions
        self.note_on_callback = None
        self.note_off_callback = None
        self.control_callback = None
    
    def initialize(self):
        """Initialize pygame midi and scan for available devices."""
        pygame.midi.init()
        self.scan_midi_devices()

        # Automatically open the first available MIDI input device
        if self.midi_devices:
            if success := self.open_midi_input():
                logging.info("Automatically opened first available MIDI input device")
            else:
                logging.warning("Failed to automatically open MIDI input device")
    
    def scan_midi_devices(self):
        """Scan for available MIDI input devices."""
        self.midi_devices = []
        
        # Get the number of MIDI devices
        device_count = pygame.midi.get_count()
        logging.debug(f"Found {device_count} total MIDI devices")
        
        for i in range(device_count):
            device_info = pygame.midi.get_device_info(i)
            name = device_info[1].decode("utf-8")
            interface = device_info[0].decode("utf-8")
            is_input = device_info[2]
            is_output = device_info[3]
            is_opened = device_info[4]
            
            # Log all devices for debugging
            logging.debug(f"MIDI device {i}: name='{name}', interface='{interface}', input={is_input}, output={is_output}, opened={is_opened}")
            
            if is_input:
                self.midi_devices.append({
                    "id": i,
                    "name": name,
                    "interface": interface,
                    "opened": False,
                    "input": True
                })
                logging.info(f"Found MIDI input device: {name} (id: {i})")
        
        if not self.midi_devices:
            logging.warning("No MIDI input devices found")
        else:
            logging.info(f"Found {len(self.midi_devices)} MIDI input devices")
            
        return self.midi_devices
    
    def open_midi_input(self, device_id=None):
        """Open a MIDI input device.
        
        Args:
            device_id (int): Device ID to open, or None to use the first available
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Close any existing MIDI input
        self.close_midi_input()

        try:
            return self._extracted_from_open_midi_input_15(device_id)
        except Exception as e:
            logging.error(f"Error opening MIDI input: {e}")
            self.midi_input = None
            self.midi_input_id = None
            return False

    # TODO Rename this here and in `open_midi_input`
    def _extracted_from_open_midi_input_15(self, device_id):
        # Find the first input device if not specified
        if device_id is None:
            for device in self.midi_devices:
                if device["input"]:
                    device_id = device["id"]
                    break

        # No device found
        if device_id is None:
            logging.warning("No MIDI input devices found")
            return False

        # Open the device
        self.midi_input = pygame.midi.Input(device_id)
        self.midi_input_id = device_id

        # Update device status
        for device in self.midi_devices:
            if device["id"] == device_id:
                device["opened"] = True

        logging.info(f"Opened MIDI input device id: {device_id}")
        return True
    
    def close_midi_input(self):
        """Close the current MIDI input device."""
        if self.midi_input:
            self.midi_input.close()
            
            # Update device status
            for device in self.midi_devices:
                if device["id"] == self.midi_input_id:
                    device["opened"] = False
            
            self.midi_input = None
            self.midi_input_id = None
            logging.info("Closed MIDI input device")
    
    def set_note_callbacks(self, note_on=None, note_off=None, control=None):
        """Set callback functions for note events.
        
        Args:
            note_on (callable): Function to call when a note is pressed
            note_off (callable): Function to call when a note is released
            control (callable): Function to call for control events
        """
        self.note_on_callback = note_on
        self.note_off_callback = note_off
        self.control_callback = control
    
    def process_keyboard_events(self, events):
        """Process keyboard events.
        
        Args:
            events (list): List of pygame events
            
        Returns:
            bool: False if the application should quit, True otherwise
        """
        for event in events:
            # Check for quit event
            if event.type == pygame.QUIT:
                return False
            
            # Key press
            elif event.type == pygame.KEYDOWN:
                # Escape key to quit
                if event.key == pygame.K_ESCAPE:
                    return False
                
                # Piano key
                if event.key in self.key_mapping and event.key not in self.pressed_keys:
                    note = self.key_mapping[event.key]
                    self.pressed_keys.add(event.key)
                    
                    # Call note_on callback
                    if self.note_on_callback:
                        self.note_on_callback(note, 100)  # Default velocity
                
                # Control key (everything else)
                elif self.control_callback:
                    self.control_callback('key_press', event.key)
            
            # Key release
            elif event.type == pygame.KEYUP:
                if event.key in self.key_mapping and event.key in self.pressed_keys:
                    note = self.key_mapping[event.key]
                    self.pressed_keys.remove(event.key)
                    
                    # Call note_off callback
                    if self.note_off_callback:
                        self.note_off_callback(note)
        
        return True
    
    def process_midi_input(self):
        """Process MIDI input messages.
        
        Returns:
            bool: True if any MIDI messages were processed
        """
        if not self.midi_input:
            return False

        # Check if there are any MIDI events
        if self.midi_input.poll():
            # Read all pending MIDI events in bursts
            event_limit = getattr(self, "max_midi_events", 32)
            midi_events = []
            while self.midi_input.poll():
                midi_events.extend(self.midi_input.read(event_limit))
            
            for event in midi_events:
                data = event[0]
                timestamp = event[1]
                
                # Parse the MIDI message
                status = data[0] & 0xF0  # Status byte (top 4 bits)
                channel = data[0] & 0x0F  # Channel (bottom 4 bits)
                
                # Note On event (0x90)
                if status == 0x90 and data[2] > 0:  # Note on with velocity > 0
                    note = data[1]
                    velocity = data[2]
                    
                    logging.debug(f"MIDI Note On: note={note}, velocity={velocity}, channel={channel}")
                    
                    # Call note_on callback
                    if self.note_on_callback:
                        self.note_on_callback(note, velocity)
                
                # Note Off event (0x80 or 0x90 with velocity=0)
                elif status == 0x80 or (status == 0x90 and data[2] == 0):
                    note = data[1]
                    
                    # Call note_off callback
                    if self.note_off_callback:
                        self.note_off_callback(note)
                
                # Control Change event (0xB0)
                elif status == 0xB0 and self.control_callback:
                    controller = data[1]
                    value = data[2]
                    self.control_callback('midi_cc', controller, value, channel)
            
            return True
            
        return False
    
    def process_input(self):
        """Process all input sources.
        
        Returns:
            bool: False if the application should quit, True otherwise
        """
        # Process keyboard events
        events = pygame.event.get()
        if not self.process_keyboard_events(events):
            return False
            
        # Process MIDI input
        self.process_midi_input()
        
        return True
    
    def cleanup(self):
        """Release all resources."""
        self.close_midi_input()
        pygame.midi.quit()

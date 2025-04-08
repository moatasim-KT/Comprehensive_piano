"""
Audio Engine module for the Comprehensive Piano Application
Handles sound generation, playback, and audio effects
"""
import pygame
import numpy as np
import threading
import queue
import sounddevice as sd
from scipy import signal
import os
import logging
from typing import Dict, List, Optional, Any, Tuple

class AudioEngine:
    """Advanced audio engine with sample playback and synthesis capabilities."""
    
    def __init__(self, sample_rate=44100):
        """Initialize the audio engine.
        
        Args:
            sample_rate (int): Sample rate for audio processing
        """
        self.sample_rate = sample_rate
        self.piano_samples = {}  # Loaded sound samples
        self.synth_sounds = {}   # Synthesized sounds
        self.active_sounds = {}  # Currently playing sounds
        self.sound_queue = queue.Queue()  # For async sound processing
        
        # Audio settings
        self.volume = 0.7
        self.reverb_amount = 0.2
        
        # Threading control
        self.audio_lock = threading.Lock()
        self.running = True
        
        # Callback functions
        self.note_on_callback = None
        self.note_off_callback = None
        
        # Flag to track sample loading status
        self.samples_loaded = False
    
    def initialize(self):
        """Initialize the audio system and load resources."""
        # Initialize pygame mixer
        pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=2, buffer=512)
        
        # Load piano samples
        self.load_samples()
        
        # Generate synth sounds for notes that don't have samples
        self.generate_synth_sounds()
        
        # Start audio processing thread
        self.audio_thread = threading.Thread(
            target=self._audio_processing_thread, 
            daemon=True
        )
        self.audio_thread.start()
        
        logging.info("Audio engine initialized")
    
    def load_samples(self, samples_dir="assets/samples"):
        """Load piano sound samples from directory.
        
        Args:
            samples_dir (str): Directory containing piano samples
        """
        self.samples_loaded = False
        
        # Create samples directory if it doesn't exist
        if not os.path.exists(samples_dir):
            os.makedirs(samples_dir)
            logging.info(f"Created samples directory: {samples_dir}")
            # No samples to load yet
            self.samples_loaded = True
            return
        
        # Clear existing samples
        self.piano_samples = {}
        
        try:
            # Load each sample file
            sample_files = [f for f in os.listdir(samples_dir) if f.endswith(('.wav', '.mp3', '.ogg'))]
            
            for filename in sample_files:
                # Extract note number from filename (e.g., "piano_60.wav" -> 60)
                try:
                    note = int(filename.split('_')[1].split('.')[0])
                    sound = pygame.mixer.Sound(os.path.join(samples_dir, filename))
                    self.piano_samples[note] = sound
                    logging.debug(f"Loaded sample: {filename} for note {note}")
                except (ValueError, IndexError) as e:
                    logging.warning(f"Could not parse note number from {filename}: {e}")
            
            logging.info(f"Loaded {len(self.piano_samples)} piano samples")
        except Exception as e:
            logging.error(f"Error loading samples: {e}")
        
        self.samples_loaded = True
    
    def generate_synth_sounds(self, first_note=21, last_note=108):
        """Generate synthesized sounds for all notes in the range.
        
        Args:
            first_note (int): First MIDI note to generate
            last_note (int): Last MIDI note to generate
        """
        for note in range(first_note, last_note + 1):
            self._generate_synth_sound(note)
        
        logging.info(f"Generated {len(self.synth_sounds)} synthesized sounds")
    
    def _generate_synth_sound(self, note, velocity=127):
        """Generate a synthesized sound for a specific note.
        
        Args:
            note (int): MIDI note number
            velocity (int): MIDI velocity (0-127)
        """
        # Calculate frequency using equal temperament formula
        frequency = 440.0 * (2.0 ** ((note - 69) / 12.0))
        
        # Generate parameters based on the note
        duration = 4.0  # seconds
        amplitude = min(1.0, velocity / 127)
        
        # Generate sound with overtones for a piano-like sound
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples, False)
        
        # Base sine wave at the fundamental frequency
        wave = np.sin(2 * np.pi * frequency * t) * 0.7
        
        # Add harmonics with decreasing amplitude
        harmonics = [
            (2, 0.35),  # 1st overtone (2x frequency)
            (3, 0.15),  # 2nd overtone
            (4, 0.07),  # 3rd overtone
            (5, 0.05),  # 4th overtone
        ]
        
        for harmonic, amp in harmonics:
            wave += np.sin(2 * np.pi * frequency * harmonic * t) * amp
        
        # Apply envelope for a piano-like sound (ADSR)
        attack = int(0.01 * self.sample_rate)  # 10ms attack
        decay = int(0.1 * self.sample_rate)    # 100ms decay
        sustain_level = 0.7                   # Sustain at 70% of peak
        release = int(2.5 * self.sample_rate)  # 2.5s release
        
        # Create envelope
        envelope = np.ones(samples) * sustain_level
        # Attack
        envelope[:attack] = np.linspace(0, 1, attack)
        # Decay
        decay_end = attack + decay
        envelope[attack:decay_end] = np.linspace(1, sustain_level, decay)
        # Release
        release_start = samples - release
        if release_start > decay_end:
            envelope[release_start:] = np.linspace(sustain_level, 0, release)
        
        # Apply envelope and normalize
        wave = wave * envelope * amplitude
        
        # Convert to 16-bit PCM
        wave = np.clip(wave, -0.99, 0.99)
        audio_data = (wave * 32767).astype(np.int16)
        
        # Create stereo sound
        stereo_data = np.column_stack((audio_data, audio_data))
        
        # Create sound object
        sound = pygame.sndarray.make_sound(stereo_data)
        self.synth_sounds[note] = sound
        
        return sound
    
    def set_note_callbacks(self, note_on_callback, note_off_callback):
        """Set callbacks for note on/off events.
        
        Args:
            note_on_callback: Function to call when a note is played
            note_off_callback: Function to call when a note is stopped
        """
        self.note_on_callback = note_on_callback
        self.note_off_callback = note_off_callback
    
    def play_note(self, note, velocity=127):
        """Play a note with the given velocity.
        
        Args:
            note (int): MIDI note number
            velocity (int): MIDI velocity (0-127)
        """
        if not 0 <= note <= 127:
            return
        
        # Scale velocity to pygame volume (0.0 to 1.0)
        volume = (velocity / 127) * self.volume
        
        # Get the sound (from samples if available, otherwise synthesized)
        sound = None
        
        # Try to use a sample first
        if note in self.piano_samples:
            sound = self.piano_samples[note]
        # Otherwise use a synthesized sound
        elif note in self.synth_sounds:
            sound = self.synth_sounds[note]
        # Generate a sound if needed
        else:
            sound = self._generate_synth_sound(note, velocity)
        
        # Stop any previous instance of this note
        self.stop_note(note, release=True)
        
        # Play the sound
        sound.set_volume(volume)
        self.active_sounds[note] = sound.play()
        
        # Call the callback if set
        if self.note_on_callback:
            self.note_on_callback(note, velocity)
    
    def stop_note(self, note, release=False):
        """Stop a note from playing.
        
        Args:
            note (int): MIDI note number
            release (bool): Whether to apply a release envelope
        """
        if note in self.active_sounds and self.active_sounds[note]:
            # Apply release if requested (fade out)
            if release:
                self.active_sounds[note].fadeout(150)  # 150ms fadeout
            else:
                self.active_sounds[note].stop()
            
            # Remove from active sounds
            del self.active_sounds[note]
            
            # Call the callback if set
            if self.note_off_callback:
                self.note_off_callback(note)
    
    def _audio_processing_thread(self):
        """Background thread for audio processing."""
        while self.running:
            try:
                # Process any sounds in the queue
                while not self.sound_queue.empty():
                    with self.audio_lock:
                        action, data = self.sound_queue.get_nowait()
                        
                        if action == "play":
                            note, velocity = data
                            self.play_note(note, velocity)
                        elif action == "stop":
                            note = data
                            self.stop_note(note)
                
                # Sleep to avoid hogging CPU
                pygame.time.wait(5)  # 5ms sleep
                
            except Exception as e:
                logging.error(f"Error in audio processing thread: {e}")
    
    def queue_note_on(self, note, velocity=127):
        """Queue a note to be played asynchronously.
        
        Args:
            note (int): MIDI note number
            velocity (int): MIDI velocity (0-127)
        """
        self.sound_queue.put(("play", (note, velocity)))
    
    def queue_note_off(self, note):
        """Queue a note to be stopped asynchronously.
        
        Args:
            note (int): MIDI note number
        """
        self.sound_queue.put(("stop", note))
    
    def set_volume(self, volume):
        """Set the global volume level.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
    
    def cleanup(self):
        """Clean up resources used by the audio engine."""
        self.running = False
        if self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)
        pygame.mixer.quit()
        logging.info("Audio engine resources cleaned up")

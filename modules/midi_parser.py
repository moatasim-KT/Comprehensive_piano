"""
MIDI Parser module for the Comprehensive Piano Application
Handles loading and parsing MIDI files
"""
import mido
import logging
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict, Counter

class MIDIAnalysisError(Exception):
    """Custom exception for MIDI analysis errors."""
    pass

class MIDIParser:
    """Enhanced MIDI file parsing with overlap handling and analysis."""
    
    def __init__(self):
        """Initialize the MIDI parser with default analysis structure."""
        self.midi_analysis = self._get_default_analysis()
        
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Return a default structure for MIDI analysis."""
        return {
            "file_path": None,
            "format": None,
            "ticks_per_beat": None,
            "num_tracks": 0,
            "total_time_seconds": 0,
            "track_names": [],
            "track_instruments": {},
            "notes": [],  # [start_time, end_time, note, velocity, track]
            "tempo_changes": [],  # [time, tempo in microsec per beat]
            "time_signature_changes": [],  # [time, numerator, denominator]
            "key_signature_changes": [],  # [time, key_sig]
            "program_changes": [],  # [time, program, track]
            "max_concurrent_notes": 0,
            "scales_detected": [],
            "chords_detected": [],
            "valid": False,
        }
    
    def parse_midi_file(self, midi_file_path: str) -> Dict[str, Any]:
        """Parse a MIDI file and return analysis data.
        
        Args:
            midi_file_path (str): Path to the MIDI file
            
        Returns:
            Dict: Analysis data containing MIDI file information
            
        Raises:
            MIDIAnalysisError: If there's an error parsing the MIDI file
        """
        try:
            return self._parse_midi_data(mido.MidiFile(midi_file_path))
        except Exception as e:
            error_msg = f"Error parsing MIDI file {midi_file_path}: {str(e)}"
            logging.error(error_msg)
            raise MIDIAnalysisError(error_msg)
    
    def _parse_midi_data(self, midi_file: mido.MidiFile) -> Dict[str, Any]:
        """Parse MIDI data from a loaded MIDI file.
        
        Args:
            midi_file (mido.MidiFile): Loaded MIDI file object
            
        Returns:
            Dict: Analysis data containing MIDI file information
        """
        # Reset the analysis
        self.midi_analysis = self._get_default_analysis()
        
        # Set basic file properties
        self.midi_analysis["file_path"] = getattr(midi_file, "filename", "unknown")
        self.midi_analysis["format"] = midi_file.type
        self.midi_analysis["ticks_per_beat"] = midi_file.ticks_per_beat
        self.midi_analysis["num_tracks"] = len(midi_file.tracks)
        
        # Track active notes to detect overlaps and chords
        active_notes = {}  # {(note, track, channel): (start_time, velocity)}
        
        # Process all tracks
        for track_idx, track in enumerate(midi_file.tracks):
            # Extract track name if available
            track_name = f"Track {track_idx}"
            for msg in track:
                if msg.type == 'track_name':
                    track_name = msg.name
                    break
            
            self.midi_analysis["track_names"].append(track_name)
            
            # Process track events
            absolute_time_ticks = 0
            current_tempo = 500000  # Default tempo (microsec per beat)
            
            for msg in track:
                # Update absolute time
                absolute_time_ticks += msg.time
                
                # Convert ticks to seconds based on current tempo
                absolute_time_seconds = mido.tick2second(
                    absolute_time_ticks, 
                    midi_file.ticks_per_beat, 
                    current_tempo
                )
                
                # Handle tempo changes
                if msg.type == 'set_tempo':
                    current_tempo = msg.tempo
                    self.midi_analysis["tempo_changes"].append(
                        [absolute_time_seconds, current_tempo]
                    )
                
                # Handle time signature changes
                elif msg.type == 'time_signature':
                    self.midi_analysis["time_signature_changes"].append(
                        [absolute_time_seconds, msg.numerator, msg.denominator]
                    )
                
                # Handle key signature changes
                elif msg.type == 'key_signature':
                    self.midi_analysis["key_signature_changes"].append(
                        [absolute_time_seconds, msg.key]
                    )
                
                # Handle program (instrument) changes
                elif msg.type == 'program_change':
                    self.midi_analysis["program_changes"].append(
                        [absolute_time_seconds, msg.program, track_idx]
                    )
                    self.midi_analysis["track_instruments"][track_idx] = msg.program
                
                # Handle note on events
                elif msg.type == 'note_on' and msg.velocity > 0:
                    # Store the start time of the note
                    note_key = (msg.note, track_idx, getattr(msg, 'channel', 0))
                    active_notes[note_key] = (absolute_time_seconds, msg.velocity)
                
                # Handle note off events
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # Try to find the matching note on event
                    # First check with exact channel match
                    note_key = (msg.note, track_idx, getattr(msg, 'channel', 0))
                    
                    if note_key in active_notes:
                        start_time, velocity = active_notes.pop(note_key)
                        # Calculate duration and add note to the list
                        duration = absolute_time_seconds - start_time
                        self.midi_analysis["notes"].append(
                            [start_time, absolute_time_seconds, msg.note, velocity, track_idx]
                        )
                    else:
                        # Try finding a match ignoring channel
                        alternate_keys = [(key, val) for key, val in active_notes.items() 
                                         if key[0] == msg.note and key[1] == track_idx]
                        
                        if alternate_keys:
                            # Use the oldest note if multiple matches
                            alternate_keys.sort(key=lambda x: x[1][0])  # Sort by start time
                            match_key, (start_time, velocity) = alternate_keys[0]
                            active_notes.pop(match_key)
                            
                            # Calculate duration and add note to the list
                            duration = absolute_time_seconds - start_time
                            self.midi_analysis["notes"].append(
                                [start_time, absolute_time_seconds, msg.note, velocity, track_idx]
                            )
                        else:
                            # As a last resort, check across all tracks (may help with some MIDI files)
                            cross_track_keys = [(key, val) for key, val in active_notes.items() 
                                              if key[0] == msg.note]
                            
                            if cross_track_keys:
                                # Use the oldest note if multiple matches
                                cross_track_keys.sort(key=lambda x: x[1][0])
                                match_key, (start_time, velocity) = cross_track_keys[0]
                                active_notes.pop(match_key)
                                
                                # When track differs, note this in the logging
                                source_track = match_key[1]
                                logging.debug(f"Cross-track note match: note {msg.note} from track {source_track} to {track_idx}")
                                
                                # Calculate duration and add note to the list
                                duration = absolute_time_seconds - start_time
                                self.midi_analysis["notes"].append(
                                    [start_time, absolute_time_seconds, msg.note, velocity, source_track]
                                )
                            else:
                                # No match found - this is a rare case that shouldn't normally happen
                                # Some MIDI files may have orphaned note-off events
                                logging.debug(f"Unmatched note-off event for note {msg.note} on track {track_idx}")
        
        # Sort notes by start time
        self.midi_analysis["notes"].sort(key=lambda x: x[0])
        
        # Find the maximum number of concurrent notes (for chord detection)
        if self.midi_analysis["notes"]:
            # Get the end time of the last note
            self.midi_analysis["total_time_seconds"] = max(
                note[1] for note in self.midi_analysis["notes"]
            )
            
            # Count active notes at any point in time
            events = []
            for note in self.midi_analysis["notes"]:
                events.append((note[0], 1))  # Start time, +1 active note
                events.append((note[1], -1))  # End time, -1 active note
            
            events.sort()
            current_count = 0
            for _, change in events:
                current_count += change
                self.midi_analysis["max_concurrent_notes"] = max(
                    self.midi_analysis["max_concurrent_notes"], 
                    current_count
                )
        
        # Basic validation
        self.midi_analysis["valid"] = len(self.midi_analysis["notes"]) > 0
        
        return self.midi_analysis
    
    def get_chords_sequence(self) -> List[Tuple[float, List[int]]]:
        """Extract a sequence of chords from MIDI data.
        
        Returns:
            List[Tuple[float, List[int]]]: List of (time, chord) tuples
        """
        if not self.midi_analysis["valid"]:
            return []
        
        # Minimum time between notes to consider them as part of the same chord (seconds)
        chord_time_threshold = 0.05
        
        # Sort notes by start time
        notes = sorted(self.midi_analysis["notes"], key=lambda x: x[0])
        
        # Group notes into chords based on start time proximity
        chords = []
        current_chord = []
        current_chord_time = 0
        
        for note in notes:
            start_time, _, note_value, velocity, _ = note
            
            # If this is the first note or the note starts close to the previous ones,
            # add it to the current chord
            if not current_chord or abs(start_time - current_chord_time) < chord_time_threshold:
                current_chord.append(note)
                # Update chord time to the average start time
                current_chord_time = sum(n[0] for n in current_chord) / len(current_chord)
            else:
                # Save the previous chord and start a new one
                chord_notes = [n[2] for n in current_chord]  # Extract just the note values
                chords.append((current_chord_time, chord_notes))
                
                # Start a new chord with the current note
                current_chord = [note]
                current_chord_time = start_time
        
        # Don't forget the last chord
        if current_chord:
            chord_notes = [n[2] for n in current_chord]
            chords.append((current_chord_time, chord_notes))
        
        return chords
    
    def get_notes_in_time_range(self, start_time: float, end_time: float) -> List[List[Any]]:
        """Get all notes that are active in a given time range.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            List[List[Any]]: List of note data [start_time, end_time, note, velocity, track]
        """
        result = []
        for note in self.midi_analysis["notes"]:
            note_start, note_end = note[0], note[1]
            # Check if the note overlaps with the requested time range
            if (note_start <= end_time and note_end >= start_time):
                result.append(note)
        return result
    
    def generate_midi_analysis_report(self) -> str:
        """Generate a human-readable report of the MIDI analysis.
        
        Returns:
            str: Formatted report
        """
        if not self.midi_analysis["valid"]:
            return "No valid MIDI data to analyze."
        
        report = []
        report.append(f"MIDI File: {self.midi_analysis['file_path']}")
        report.append(f"Format: {self.midi_analysis['format']}")
        report.append(f"Tracks: {self.midi_analysis['num_tracks']}")
        report.append(f"Duration: {self.midi_analysis['total_time_seconds']:.2f} seconds")
        report.append(f"Total notes: {len(self.midi_analysis['notes'])}")
        
        # Track information
        report.append("\nTracks:")
        for i, name in enumerate(self.midi_analysis["track_names"]):
            instrument = self.midi_analysis["track_instruments"].get(i, "Unknown")
            report.append(f"  {i}: {name} (Instrument: {instrument})")
        
        # Tempo changes
        if self.midi_analysis["tempo_changes"]:
            report.append("\nTempo Changes:")
            for time, tempo in self.midi_analysis["tempo_changes"]:
                bpm = 60000000 / tempo
                report.append(f"  {time:.2f}s: {bpm:.1f} BPM")
        
        # Time signature changes
        if self.midi_analysis["time_signature_changes"]:
            report.append("\nTime Signature Changes:")
            for time, num, denom in self.midi_analysis["time_signature_changes"]:
                report.append(f"  {time:.2f}s: {num}/{denom}")
        
        # Key signature changes
        if self.midi_analysis["key_signature_changes"]:
            report.append("\nKey Signature Changes:")
            for time, key in self.midi_analysis["key_signature_changes"]:
                report.append(f"  {time:.2f}s: {key}")
        
        return "\n".join(report)

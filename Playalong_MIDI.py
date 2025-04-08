#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import pygame.midi
import pygame.mixer  # Add this import for sound playback
import mido
import sys
import time
import numpy as np
import argparse
from collections import defaultdict, Counter, deque
import logging
import io
import random
from typing import List, Dict, Optional, Any, Set
import os  # Add os import at the top

# --- Constants ---
# Learning Mode Settings
FALLING_NOTE_SPEED = 150  # Return to original speed
TARGET_LINE_Y_OFFSET = 50  # How far above the piano keys the target line is
HIT_WINDOW_MS = 200  # Time window (milliseconds) around target time to count as a hit
PREP_TIME_SEC = 3  # Return to original prep time
DEBUG_FORCE_DISPLAY_NOTES = True  # Force notes to display even if timing is off

# --- Custom Exception ---
class MIDIAnalysisError(Exception):
    """Custom exception for MIDI analysis errors."""

    pass


# --- Note/Chord Generation ---
class MusicTheory:
    """Helper class for basic music theory elements."""

    SCALE_INTERVALS = {
        "major": [0, 2, 4, 5, 7, 9, 11, 12],  # W-W-H-W-W-W-H
        "natural_minor": [0, 2, 3, 5, 7, 8, 10, 12],  # W-H-W-W-H-W-W
        "harmonic_minor": [0, 2, 3, 5, 7, 8, 11, 12],  # W-H-W-W-H-WH-H
        "chromatic": list(range(13)),
    }
    CHORD_INTERVALS = {
        "maj": [0, 4, 7],  # Major Triad
        "min": [0, 3, 7],  # Minor Triad
        "dim": [0, 3, 6],  # Diminished Triad
        "aug": [0, 4, 8],  # Augmented Triad
        "maj7": [0, 4, 7, 11],  # Major 7th
        "min7": [0, 3, 7, 10],  # Minor 7th
        "dom7": [0, 4, 7, 10],  # Dominant 7th
        "dim7": [0, 3, 6, 9],  # Diminished 7th
        "sus4": [0, 5, 7],  # Suspended 4th
    }

    @staticmethod
    def generate_scale(
        root_note: int, scale_type: str = "major", octaves: int = 1
    ) -> List[int]:
        """Generates MIDI notes for a scale."""
        intervals = MusicTheory.SCALE_INTERVALS.get(scale_type.lower())
        if not intervals:
            logging.warning(f"Unknown scale type: {scale_type}. Defaulting to major.")
            intervals = MusicTheory.SCALE_INTERVALS["major"]

        scale_notes = []
        for o in range(octaves):
            for interval in intervals[:-1]:  # Exclude octave repetition within loop
                note = root_note + (o * 12) + interval
                if 0 <= note <= 127:
                    scale_notes.append(note)
        # Add the final octave note
        final_note = root_note + (octaves * 12)
        if 0 <= final_note <= 127:
            scale_notes.append(final_note)

        return scale_notes

    @staticmethod
    def generate_chord(root_note: int, chord_type: str = "maj") -> List[int]:
        """Generates MIDI notes for a chord."""
        intervals = MusicTheory.CHORD_INTERVALS.get(chord_type.lower())
        if not intervals:
            logging.warning(
                f"Unknown chord type: {chord_type}. Defaulting to major triad."
            )
            intervals = MusicTheory.CHORD_INTERVALS["maj"]

        chord_notes = []
        for interval in intervals:
            note = root_note + interval
            if 0 <= note <= 127:
                chord_notes.append(note)
        return chord_notes


# --- Falling Note Class ---
class FallingNote:
    """Represents a note to be played in learning mode."""

    def __init__(
        self,
        note: int,
        start_time_sec: float,
        duration_sec: float,
        target_y: int,
        screen_height: int,
        velocity: int = 127  # new: capture velocity
    ):
        self.note = note
        self.start_time_sec = start_time_sec
        self.end_time_sec = start_time_sec + duration_sec
        self.duration_sec = duration_sec
        self.target_y = target_y
        self.velocity = velocity  # new: store velocity
        # Height remains proportional to duration.
        self.note_height = max(20, self.duration_sec * FALLING_NOTE_SPEED)
        self.start_y = target_y - (FALLING_NOTE_SPEED * start_time_sec)
        self.current_y = self.start_y - (screen_height + self.note_height + 100)
        self.rect = None
        self.state = "upcoming"  # upcoming, active, hit, missed, invalid_key
        self.hit_time_ms: Optional[int] = None
        self._note_name_cache = AdvancedMIDIParser._get_note_name_static(
            note
        )  # Cache note name

    # Static method added to FallingNote for easier access in check_hit logging
    @staticmethod
    def get_note_name(note: int) -> str:
        """Gets the standard note name (e.g., C#4) using the static method."""
        return AdvancedMIDIParser._get_note_name_static(note)

    # *** Method Updated with Enhanced Debug Logging ***
    def update(self, current_time_sec: float, key_rect_map: Dict[int, pygame.Rect]):
        """Update the note's vertical position and state."""
        key_rect = key_rect_map.get(self.note)
        if not key_rect:
            if self.state != "invalid_key":
                # Log only once when it becomes invalid
                logging.debug(f"Note {self.note} ({self._note_name_cache}) is outside the displayed piano range. Marking as invalid.")
                self.state = "invalid_key"
            return  # Cannot update position if key doesn't exist on piano

        # Calculate time remaining until hit
        time_to_hit_sec = self.start_time_sec - current_time_sec

        # Calculate vertical position based on time
        # Notes start above the screen and move downward
        self.current_y = self.target_y - (time_to_hit_sec * FALLING_NOTE_SPEED)

        # Ensure note is visible when close to hitting the target line
        if abs(time_to_hit_sec) < 10:  # Only log notes within 10 seconds of hitting
            logging.debug(f"Note {self.note} ({self._note_name_cache}) - time_to_hit: {time_to_hit_sec:.2f}s, y: {self.current_y}")

        # Calculate height based on duration
        height = max(20, self.duration_sec * FALLING_NOTE_SPEED)
        width = key_rect.width - 4  # Make slightly narrower than the key for better visual

        # Make sure the note's position is relative to the key it corresponds to
        center_x = key_rect.centerx
        
        # Create the rectangle for the note
        self.rect = pygame.Rect(
            center_x - width // 2, self.current_y - height, width, height
        )

        # Update state based on time, only if not already hit/missed/invalid
        if self.state not in ["hit", "missed", "invalid_key"]:
            current_time_ms = int(current_time_sec * 1000)
            start_time_ms = int(self.start_time_sec * 1000)
            previous_state = self.state  # Save for logging state transitions

            # Check for missed state (if current time is significantly past the hit window end)
            if current_time_ms > (start_time_ms + HIT_WINDOW_MS):
                if self.state != "missed":  # Log only on state change
                    logging.debug(
                        f"Note {self.note} ({self._note_name_cache}) changed state: {previous_state} -> MISSED. "
                        f"Current time {current_time_ms}ms > Target time {start_time_ms}ms + Window {HIT_WINDOW_MS}ms"
                    )
                self.state = "missed"
            # Check for active state (within the hit window)
            elif abs(current_time_ms - start_time_ms) <= HIT_WINDOW_MS:
                if self.state != "active":  # Log only on state change
                    logging.debug(
                        f"Note {self.note} ({self._note_name_cache}) changed state: {previous_state} -> ACTIVE. "
                        f"Current time {current_time_ms}ms, Target time {start_time_ms}ms, Diff: {current_time_ms - start_time_ms}ms"
                    )
                self.state = "active"
            # Otherwise, it's upcoming
            else:
                # Only log if state actually changed
                if self.state != "upcoming" and previous_state != "upcoming":
                    logging.debug(
                        f"Note {self.note} ({self._note_name_cache}) changed state: {previous_state} -> UPCOMING. "
                        f"Current time {current_time_ms}ms, Target time {start_time_ms}ms, Time to hit: {time_to_hit_sec:.3f}s"
                    )
                self.state = "upcoming"

    def draw(self, screen, colors, font):
        """Draw the falling note with the label inside."""
        # Always draw notes, regardless of state or position
        if self.rect is None:
            return
        
        # --- Determine Color and Border ---
        # Use bright, high-contrast colors that will be clearly visible
        color = colors.get("falling_note_upcoming", (50, 150, 255))  # Bright blue
        border_color = colors.get("falling_note_border", (0, 0, 0))  # Black
        text_color = colors.get("key_text", (0, 0, 0))  # Black
        
        if self.state == "active":
            color = colors.get("falling_note_active", (255, 50, 50))  # Bright red
        elif self.state == "hit":
            color = colors.get("falling_note_hit", (50, 255, 50))  # Bright green
        elif self.state == "missed":
            color = colors.get("falling_note_missed", (200, 200, 200))  # Gray
        
        # --- Draw with extra visibility ---
        # Make the note larger and more prominent
        visible_rect = pygame.Rect(
            self.rect.left - 2, 
            self.rect.top - 2, 
            self.rect.width + 4, 
            self.rect.height + 4
        )
        
        # Fill the note
        pygame.draw.rect(screen, color, visible_rect)
        # Add a border for contrast
        pygame.draw.rect(screen, border_color, visible_rect, 2)
        
        # --- Draw the note name text ---
        # Make sure text fits within the note
        if visible_rect.height > 20 and visible_rect.width > 15:
            text_surf = font.render(self._note_name_cache, True, text_color)
            text_rect = text_surf.get_rect(center=visible_rect.center)
            
            # Draw outline around text for better readability
            for offset in [(1,1), (-1,-1), (1,-1), (-1,1)]:
                outline_rect = text_rect.copy()
                outline_rect.x += offset[0]
                outline_rect.y += offset[1]
                outline_text = font.render(self._note_name_cache, True, border_color)
                screen.blit(outline_text, outline_rect)
                
            # Draw the text
            screen.blit(text_surf, text_rect)
    
    # *** Method Updated with Enhanced Debug Logging and Fixed Timing ***
    def check_hit(self, played_note: int, play_time_ms: int) -> bool:
        """Check if this note was hit correctly."""
        if self.state in ["upcoming", "active"]:
            # Basic checks
            is_match = played_note == self.note
            if not is_match:
                logging.debug(f"Note mismatch: Played {self.get_note_name(played_note)} but expected {self._note_name_cache}")
                return False

            # More lenient timing check
            start_time_ms = int(self.start_time_sec * 1000)
            time_diff = abs(play_time_ms - start_time_ms)
            
            # Accept hits within a more generous window
            if time_diff <= 500:  # Half a second window
                logging.debug(
                    f"HIT registered for {self._note_name_cache} "
                    f"(Time diff: {time_diff}ms, State: {self.state})"
                )
                self.state = "hit"
                self.hit_time_ms = play_time_ms
                return True
            else:
                logging.debug(
                    f"Hit timing outside window for {self._note_name_cache} "
                    f"(Time diff: {time_diff}ms, State: {self.state})"
                )

        elif self.state == "hit":
            logging.debug(f"Note {self._note_name_cache} already hit at {self.hit_time_ms}ms")
        elif self.state == "missed":
            logging.debug(f"Attempted to hit missed note {self._note_name_cache}")
        else:
            logging.debug(f"Cannot hit note {self._note_name_cache} in state {self.state}")
        
        return False

    # TODO Rename this here and in `check_hit`
    def _extracted_from_check_hit_27(self, play_time_ms):
        # --- Enhanced Debug Logging ---
        old_state = self.state
        logging.debug(
            f"  >>> HIT REGISTERED for {self._note_name_cache}! Changing state from {old_state} to hit."
        )
        # --- End Enhanced Debug Logging ---
        self.state = "hit"
        self.hit_time_ms = play_time_ms  # Record hit time

        # --- Enhanced Debug Logging ---
        logging.debug(
            f"  >>> VERIFICATION: Note {self._note_name_cache} state is now '{self.state}' (was '{old_state}')"
        )
        # --- End Enhanced Debug Logging ---
        return True


# =========================================================
# AdvancedMIDIParser Class (Unchanged from previous version)
# =========================================================
class AdvancedMIDIParser:
    """Enhanced MIDI file parsing with overlap handling."""

    def __init__(self):
        self.midi_analysis = self._get_default_analysis()
        # Logging configured by main app

    def _get_default_analysis(self) -> Dict[str, Any]:
        return {
            "total_notes": 0,
            "unique_notes": set(),
            "note_distribution": defaultdict(int),
            "note_duration_stats": {
                "min_duration": float("inf"),
                "max_duration": 0.0,
                "avg_duration": 0.0,
            },
            "tempo_changes": [],
            "key_signature_changes": [],
            "time_signature_changes": [],
            "program_changes": defaultdict(list),
            "total_duration": 0.0,
            "ticks_per_beat": None,
            "filename": None,
            "tracks": [],
            "default_tempo": 500000,
            "timed_notes": [],  # List of {"note", "start_sec", "duration_sec", "velocity", "track", "channel"}
        }

    def parse_midi_file(self, midi_file_path: str) -> Dict[str, Any]:
        try:
            return self._extracted_from_parse_midi_file_3(midi_file_path)
        except FileNotFoundError as e:
            logging.error(f"MIDI file not found: {midi_file_path}")
            raise MIDIAnalysisError(f"MIDI file not found: {midi_file_path}") from e
        except Exception as e:
            logging.exception(
                f"Unexpected error parsing MIDI file '{midi_file_path}': {e}"
            )
            raise MIDIAnalysisError(f"Error parsing MIDI file: {e}") from e

    def _extracted_from_parse_midi_file_3(self, midi_file_path):
        self.midi_analysis = self._get_default_analysis()  # Reset analysis
        logging.debug(f"Attempting to parse MIDI file: {midi_file_path}")
        try:
            midi_file = mido.MidiFile(midi_file_path)
        except Exception as e:
            logging.exception(f"Mido failed to open or parse {midi_file_path}")
            raise MIDIAnalysisError(
                f"Mido parsing error for {midi_file_path}: {e}"
            ) from e

        logging.debug(
            f"Mido opened file. Type: {midi_file.type}, Length: {midi_file.length:.2f}s, Ticks/Beat: {midi_file.ticks_per_beat}"
        )
        if midi_file.ticks_per_beat is None or midi_file.ticks_per_beat == 0:
            logging.warning(
                "MIDI file has invalid or missing ticks_per_beat. Using default 480."
            )
        return self._parse_midi_data(midi_file)

    def _parse_midi_data(self, midi_file: mido.MidiFile) -> Dict[str, Any]:
        # sourcery skip: low-code-quality
        self.midi_analysis["ticks_per_beat"] = midi_file.ticks_per_beat or 480
        self.midi_analysis["filename"] = midi_file.filename
        absolute_tick_max = 0
        current_tempo = self.midi_analysis["default_tempo"]
        timed_notes = []

        # --- Tempo Handling: Find first tempo globally ---
        initial_tempo_found = False
        for track in midi_file.tracks:
            for msg in track:
                if msg.is_meta and msg.type == "set_tempo":
                    current_tempo = msg.tempo
                    logging.debug(
                        f"Found initial tempo {current_tempo} ({mido.tempo2bpm(current_tempo):.2f} BPM)"
                    )
                    initial_tempo_found = True
                    break
            if initial_tempo_found:
                break
        if not initial_tempo_found:
            logging.debug(
                f"No initial tempo found, using default {current_tempo} ({mido.tempo2bpm(current_tempo):.2f} BPM)"
            )

        # --- Process Tracks ---
        for track_num, track in enumerate(midi_file.tracks):
            track_name = track.name or f"Track {track_num}"
            self.midi_analysis["tracks"].append(track_name)
            logging.debug(f"Processing {track_name}...")
            absolute_tick_track = 0
            # active_notes_ticks: { (note, channel) : (start_tick, start_tempo, velocity) }
            active_notes_ticks = {}
            track_tempo = (
                current_tempo  # Each track starts with the initial global tempo
            )

            for msg in track:
                # --- Time Calculation ---
                delta_ticks = msg.time
                absolute_tick_track += delta_ticks
                # Use the track's current tempo for time calculation at this point
                current_time_sec_at_msg = mido.tick2second(
                    absolute_tick_track,
                    self.midi_analysis["ticks_per_beat"],
                    track_tempo,
                )

                # --- Meta Messages ---
                if msg.is_meta:
                    if msg.type == "key_signature":
                        self.midi_analysis["key_signature_changes"].append(
                            {
                                "time_seconds": current_time_sec_at_msg,
                                "tick": absolute_tick_track,
                                "key": msg.key,
                            }
                        )
                    elif msg.type == "set_tempo":
                        old_tempo = track_tempo
                        track_tempo = (
                            msg.tempo
                        )  # Update tempo for subsequent calculations IN THIS TRACK
                        bpm = mido.tempo2bpm(track_tempo)
                        logging.debug(
                            f"    T{track_num} Tempo Change at tick {absolute_tick_track}: {old_tempo} -> {track_tempo} ({bpm:.2f} BPM)"
                        )
                        self.midi_analysis["tempo_changes"].append(
                            {
                                "time_seconds": current_time_sec_at_msg,
                                "tick": absolute_tick_track,
                                "tempo": track_tempo,
                                "bpm": bpm,
                            }
                        )
                        # Re-calculate current time based on the NEW tempo from this point forward
                        current_time_sec_at_msg = mido.tick2second(
                            absolute_tick_track,
                            self.midi_analysis["ticks_per_beat"],
                            track_tempo,
                        )
                    elif msg.type == "time_signature":
                        self.midi_analysis["time_signature_changes"].append(
                            {
                                "time_seconds": current_time_sec_at_msg,
                                "tick": absolute_tick_track,
                                "numerator": msg.numerator,
                                "denominator": msg.denominator,
                            }
                        )
                    # Ignore other meta messages for timed notes

                elif msg.type == "program_change":
                    self.midi_analysis["program_changes"][track_num].append(
                        {
                            "time_seconds": current_time_sec_at_msg,
                            "tick": absolute_tick_track,
                            "program": msg.program,
                            "channel": msg.channel,
                        }
                    )

                elif msg.type == "note_on" and msg.velocity > 0:
                    note_key = (msg.note, msg.channel)
                    if note_key in active_notes_ticks:
                        # Overlap: Log warning but keep the original note active for timing simplicity
                        logging.warning(
                            f"    T{track_num} Note On received for already active key {note_key} at tick {absolute_tick_track}. Ignoring this Note On for timing, waiting for Note Off."
                        )
                        # Optional: Could end the previous note here and start a new one if strict re-triggering is needed
                    else:
                        # New Note On: Store start tick, tempo AT THE START, velocity
                        active_notes_ticks[note_key] = (
                            absolute_tick_track,
                            track_tempo,
                            msg.velocity,
                        )
                        logging.debug(
                            f"    T{track_num} Note On: {note_key} Vel: {msg.velocity} at tick {absolute_tick_track}, tempo {track_tempo}"
                        )
                        # Update basic stats
                        self.midi_analysis["unique_notes"].add(msg.note)
                        self.midi_analysis["note_distribution"][msg.note] += 1
                        self.midi_analysis["total_notes"] += 1

                elif msg.type == "note_off" or (
                    msg.type == "note_on" and msg.velocity == 0
                ):
                    note_key = (msg.note, msg.channel)
                    if note_key in active_notes_ticks:
                        # Found matching Note On: Calculate duration and times
                        start_tick, start_tempo, start_velocity = (
                            active_notes_ticks.pop(note_key)
                        )  # Remove from active
                        end_tick = absolute_tick_track
                        duration_ticks = end_tick - start_tick

                        # CRITICAL: Calculate start time and duration using the TEMPO AT THE START of the note
                        note_start_time_sec = mido.tick2second(
                            start_tick, self.midi_analysis["ticks_per_beat"], start_tempo
                        )
                        duration_seconds = mido.tick2second(
                            duration_ticks,
                            self.midi_analysis["ticks_per_beat"],
                            start_tempo,
                        )

                        logging.debug(
                            f"    T{track_num} Note Off: {note_key} at tick {end_tick}. Start tick: {start_tick}, Dur Ticks: {duration_ticks}, Start Tempo: {start_tempo}, Dur Sec: {duration_seconds:.3f}, Start Sec: {note_start_time_sec:.3f}"
                        )

                        # Add to timed_notes if duration is positive
                        if (
                            duration_seconds > 0.001
                        ):  # Use a small threshold to avoid zero-duration noise
                            timed_notes.append(
                                {
                                    "note": msg.note,
                                    "start_sec": note_start_time_sec,
                                    "duration_sec": duration_seconds,
                                    "velocity": start_velocity,
                                    "track": track_num,
                                    "channel": msg.channel,
                                }
                            )
                            # Update global duration stats
                            self.midi_analysis["note_duration_stats"][
                                "min_duration"
                            ] = min(
                                self.midi_analysis["note_duration_stats"][
                                    "min_duration"
                                ],
                                duration_seconds,
                            )
                            self.midi_analysis["note_duration_stats"][
                                "max_duration"
                            ] = max(
                                self.midi_analysis["note_duration_stats"][
                                    "max_duration"],
                                duration_seconds,
                            )
                        else:
                            logging.warning(
                                f"    T{track_num} Zero or near-zero duration ({duration_seconds:.4f}) calculated for note {note_key} ending at tick {end_tick}. Start tick {start_tick}. Ignoring note."
                            )
                    else:  # Note off without matching Note On
                        logging.debug(
                            f"    T{track_num} Ignoring Note Off for {note_key} at tick {absolute_tick_track} - no matching active Note On found."
                        )

            # --- End of Track: Handle Notes Still On ---
            # Use the final tempo of this track for end time calculation
            end_time_sec_track = mido.tick2second(
                absolute_tick_track, self.midi_analysis["ticks_per_beat"], track_tempo
            )
            if active_notes_ticks:
                logging.debug(
                    f"  End of {track_name}: Handling {len(active_notes_ticks)} notes still active (no Note Off found). Track end tick {absolute_tick_track}"
                )
                for note_key, (start_tick, start_tempo, start_velocity) in list(
                    active_notes_ticks.items()
                ):
                    duration_ticks = absolute_tick_track - start_tick
                    # Calculate duration and start time using the tempo WHEN THE NOTE STARTED
                    note_start_time_sec = mido.tick2second(
                        start_tick, self.midi_analysis["ticks_per_beat"], start_tempo
                    )
                    duration_seconds = mido.tick2second(
                        duration_ticks,
                        self.midi_analysis["ticks_per_beat"],
                        start_tempo,
                    )

                    note, channel = note_key
                    logging.debug(
                        f"    Ending active note {note_key} at track end. Start tick: {start_tick}, Dur Ticks: {duration_ticks}, Start Tempo: {start_tempo}, Dur Sec: {duration_seconds:.3f}, Start Sec: {note_start_time_sec:.3f}"
                    )
                    if duration_seconds > 0.001:
                        timed_notes.append(
                            {
                                "note": note,
                                "start_sec": note_start_time_sec,
                                "duration_sec": duration_seconds,
                                "velocity": start_velocity,
                                "track": track_num,
                                "channel": channel,
                            }
                        )
                        self.midi_analysis["note_duration_stats"]["min_duration"] = min(
                            self.midi_analysis["note_duration_stats"]["min_duration"],
                            duration_seconds,
                        )
                        self.midi_analysis["note_duration_stats"]["max_duration"] = max(
                            self.midi_analysis["note_duration_stats"]["max_duration"],
                            duration_seconds,
                        )
                    else:
                        logging.warning(
                            f"    Zero duration calculated for note {note_key} active at track end. Ignoring."
                        )
                    active_notes_ticks.pop(note_key)  # Remove handled note

            absolute_tick_max = max(absolute_tick_max, absolute_tick_track)

        # --- Final Calculations ---
        # Determine the tempo active at the very end of the longest track for total duration
        final_tempo = self.midi_analysis["default_tempo"]
        if self.midi_analysis["tempo_changes"]:
            if last_tempo_change := max(
                (
                    tc
                    for tc in self.midi_analysis["tempo_changes"]
                    if tc["tick"] <= absolute_tick_max
                ),
                key=lambda tc: tc["tick"],
                default=None,
            ):
                final_tempo = last_tempo_change["tempo"]
            elif (
                self.midi_analysis["tempo_changes"][0]["tick"] > 0
            ):  # If first change is after tick 0
                # Use default tempo if max tick is before first change
                if absolute_tick_max < self.midi_analysis["tempo_changes"][0]["tick"]:
                    final_tempo = self.midi_analysis["default_tempo"]
                else:  # Should be covered by max() logic, but as fallback
                    final_tempo = self.midi_analysis["tempo_changes"][0][
                        "tempo"
                    ]  # Or maybe error?
            else:
                final_tempo = self.midi_analysis["tempo_changes"][0]["tempo"]

        self.midi_analysis["total_duration"] = mido.tick2second(
            absolute_tick_max, self.midi_analysis["ticks_per_beat"], final_tempo
        )

        if timed_notes:
            total_duration_sum_sec = sum(n["duration_sec"] for n in timed_notes)
            self.midi_analysis["note_duration_stats"]["avg_duration"] = (
                total_duration_sum_sec / len(timed_notes)
            )
        else:
            self.midi_analysis["note_duration_stats"]["avg_duration"] = 0.0
        if self.midi_analysis["note_duration_stats"]["min_duration"] == float("inf"):
            self.midi_analysis["note_duration_stats"]["min_duration"] = 0.0

        # Sort timed notes by start time and store
        self.midi_analysis["timed_notes"] = sorted(
            timed_notes, key=lambda x: x["start_sec"]
        )
        logging.info(
            f"Finished parsing. Total timed notes extracted: {len(self.midi_analysis['timed_notes'])}"
        )
        if (
            not self.midi_analysis["timed_notes"]
            and self.midi_analysis["total_notes"] > 0
        ):
            logging.warning(
                "Parsing found Note On events but resulted in zero timed notes (check durations/logic)."
            )

        return self.midi_analysis

    # --- Report Generation Methods (Unchanged) ---
    def generate_midi_analysis_report(self) -> str:
        analysis = self.midi_analysis
        if not analysis or analysis.get("filename") is None:
            return "No MIDI analysis data available."
        report = (
            f"### MIDI File Analysis Report: {analysis.get('filename', 'N/A')} ###\n\n"
        )
        report += self._generate_general_info(analysis)
        report += self._generate_note_info(analysis)
        report += self._generate_duration_stats(analysis)
        report += self._generate_tempo_changes(analysis)
        report += self._generate_time_signature_changes(analysis)
        report += self._generate_key_signature_changes(analysis)
        report += self._generate_program_changes(analysis)
        return report

    def _generate_general_info(self, analysis):
        info = f"Approx. Total Duration: {analysis.get('total_duration', 'N/A'):.2f} seconds\n"
        info += f"Ticks Per Beat: {analysis.get('ticks_per_beat', 'N/A')}\n"
        info += f"Number of Tracks: {len(analysis.get('tracks', []))}\n"
        track_names = analysis.get("tracks", [])
        info += f"Tracks: {', '.join(track_names) if track_names else 'N/A'}\n\n"
        return info

    def _generate_note_info(self, analysis):
        timed_notes_count = len(analysis.get("timed_notes", []))
        info = f"Total Notes Played (raw NoteOn): {analysis['total_notes']}\n"
        info += f"Notes in Sequence (Timed): {timed_notes_count}\n"
        info += f"Unique Notes Used: {len(analysis['unique_notes'])}\n"
        if analysis["unique_notes"]:
            min_note, max_note = min(analysis["unique_notes"]), max(
                analysis["unique_notes"]
            )
            info += f"Note Range: {min_note} ({self._get_note_name_static(min_note)}) - {max_note} ({self._get_note_name_static(max_note)})\n\n"
            if analysis["note_distribution"]:
                sorted_notes = sorted(
                    analysis["note_distribution"].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:5]
                info += (
                    "Most Frequent Notes (Top 5):\n"
                    + "\n".join(
                        [
                            f"  Note {n} ({self._get_note_name_static(n)}): {c} times"
                            for n, c in sorted_notes
                        ]
                    )
                    + "\n"
                )
            else:
                info += "Most Frequent Notes: N/A\n"
        else:
            info += "Note Range: N/A\nMost Frequent Notes: N/A\n"
        return info + "\n"

    def _generate_duration_stats(self, analysis):
        stats = analysis["note_duration_stats"]
        min_d = (
            f"{stats['min_duration']:.4f}"
            if stats["min_duration"] is not None
            and stats["min_duration"] != float("inf")
            else "N/A"
        )
        max_d = (
            f"{stats['max_duration']:.4f}"
            if stats["max_duration"] is not None
            else "N/A"
        )
        avg_d = (
            f"{stats['avg_duration']:.4f}"
            if stats["avg_duration"] is not None
            else "N/A"
        )
        s = "Note Duration Statistics (Timed Notes):\n"
        s += f"  Min Duration: {min_d}\n  Max Duration: {max_d}\n  Avg Duration: {avg_d}\n\n"
        return s

    def _generate_tempo_changes(self, analysis):
        changes = "Tempo Changes (BPM):\n"
        default_bpm = mido.tempo2bpm(analysis.get("default_tempo", 500000))
        if tempo_events := sorted(
            analysis.get("tempo_changes", []), key=lambda x: x["tick"]
        ):
            last_bpm = -1  # Force printing the first one
            # Report default if first change is not at tick 0
            if tempo_events[0]["tick"] > 0:
                changes += f"  Initial Tempo (Default): {default_bpm:.2f} BPM (until tick {tempo_events[0]['tick']})\n"
                last_bpm = default_bpm  # Set last_bpm so we only report the first event if it's different

            for change in tempo_events:
                bpm = change.get("bpm", mido.tempo2bpm(change["tempo"]))
                if abs(bpm - last_bpm) > 0.01:  # Check for actual change
                    changes += f"  Tick {change['tick']} ({change['time_seconds']:.2f}s): {bpm:.2f} BPM\n"
                    last_bpm = bpm
        else:
            changes += f"  No tempo changes detected (Using default/initial: {default_bpm:.2f} BPM).\n"
        return changes + "\n"

    def _generate_time_signature_changes(self, analysis):
        changes = "Time Signature Changes:\n"
        ts_events = sorted(
            analysis.get("time_signature_changes", []), key=lambda x: x["tick"]
        )
        if ts_events:
            last_sig = None
            # Report assumed 4/4 if first change not at tick 0
            if ts_events[0]["tick"] > 0:
                changes += (
                    f"  Initial (Assumed): 4/4 (until tick {ts_events[0]['tick']})\n"
                )
                last_sig = "4/4"

            for change in ts_events:
                current_sig = f"{change['numerator']}/{change['denominator']}"
                # Prefix only really needed if first isn't at tick 0, otherwise Tick 0 is fine
                prefix = f"Tick {change['tick']} ({change['time_seconds']:.2f}s):"
                if current_sig != last_sig:
                    changes += f"  {prefix} {current_sig}\n"
                    last_sig = current_sig
        else:
            changes += "  No time signature changes detected (Assumed 4/4).\n"
        return changes + "\n"

    def _generate_key_signature_changes(self, analysis):
        changes = "Key Signature Changes:\n"
        ks_events = sorted(
            analysis.get("key_signature_changes", []), key=lambda x: x["tick"]
        )
        if ks_events:
            last_key = None
            # Report assumed C Major if first change not at tick 0
            if ks_events[0]["tick"] > 0:
                changes += f"  Initial (Assumed): C Major / A Minor (until tick {ks_events[0]['tick']})\n"
                last_key = "C"  # Assuming C is the default representation

            for change in ks_events:
                if change["key"] != last_key:
                    prefix = f"Tick {change['tick']} ({change['time_seconds']:.2f}s):"
                    changes += f"  {prefix} {change['key']}\n"
                    last_key = change["key"]
        else:
            changes += (
                "  No key signature changes detected (Assumed C Major / A Minor).\n"
            )
        return changes + "\n"

    def _generate_program_changes(self, analysis):
        changes = "Program (Instrument) Changes:\n"
        prog_changes_dict = analysis.get("program_changes", {})
        if prog_changes_dict:
            for track_num, changes_list in sorted(prog_changes_dict.items()):
                track_name = (
                    analysis["tracks"][track_num]
                    if track_num < len(analysis["tracks"])
                    else f"Track {track_num}"
                )
                if changes_list:  # Only report tracks with actual changes
                    changes += f"  {track_name}:\n"
                    last_prog = -1  # Track-specific last program
                    sorted_changes_list = sorted(changes_list, key=lambda x: x["tick"])
                    for change in sorted_changes_list:
                        if change["program"] != last_prog:
                            changes += f"    Tick {change['tick']} ({change['time_seconds']:.2f}s), Ch {change['channel']}: Prog {change['program']}\n"
                            last_prog = change["program"]
        else:
            changes += "  No program changes detected.\n"
        return changes

    @staticmethod
    def _get_note_name_static(note: int) -> str:
        if not (0 <= note <= 127):
            return "??"
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (note // 12) - 1
        return f"{names[note % 12]}{octave}"


# =========================================================
# END OF AdvancedMIDIParser Class
# =========================================================


# --- Base Piano Trainer Class ---
class PianoTrainer:
    """Base class (can be empty or have common methods)"""

    def __init__(self):
        logging.debug("Initializing Base PianoTrainer...")

    def _render_ui(self):
        pass # Base implementation, can be overridden

    def run(self, mode=None, midi_file=None):
        raise NotImplementedError("Subclasses should implement the run method.")

    def _cleanup(self):
        logging.debug("Cleaning up Base PianoTrainer...")


# --- Enhanced UI and Core Logic Class (No longer nested) ---
class EnhancedPianoTrainerUI(PianoTrainer): # Inherits from PianoTrainer
    def __init__(self, *args, **kwargs):
        # --- Basic Init ---
        logging.info("Initializing EnhancedPianoTrainerUI...")
        
        # Default settings (will be overridden if passed in args/kwargs)
        self.settings = {
            "mode": "freestyle",
            "midi_file": None,
            "learning_type": "scale",
            "root_note": 60,
            "scale_chord_type": "major",
            "difficulty": "intermediate",
            "log_level": "INFO",
            "verbose": False
        }
        
        # Update settings from kwargs if provided
        for key, value in kwargs.items():
            if key in self.settings:
                self.settings[key] = value
        
        self.screen_width = 1450
        self.screen_height = 700
        
        try:
            pygame.init()
            pygame.midi.init()
            pygame.font.init()
            pygame.mixer.init()  # Initialize pygame.mixer for sound playback
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            pygame.display.set_caption("Enhanced Piano Trainer")
            
            # Setup fonts
            self.title_font = pygame.font.SysFont("Arial", 36)
            self.note_font = pygame.font.SysFont("Arial", 20)
            self.stats_font = pygame.font.SysFont("Arial", 16)
            
            # Setup colors
            self.colors = {
                "white": (255, 255, 255),
                "black": (0, 0, 0),
                "gray": (200, 200, 200),
                "light_gray": (230, 230, 230),
                "blue": (0, 0, 255),
                "red": (255, 0, 0),
                "green": (0, 255, 0),
                "light_blue": (173, 216, 230),
                "dark_green": (0, 100, 0),
                "medium_green": (60, 179, 113),
                "falling_note_upcoming": (173, 216, 255),  # Light blue
                "falling_note_active": (0, 191, 255),      # Deep sky blue
                "falling_note_hit": (50, 205, 50),         # Lime green
                "falling_note_missed": (255, 69, 0),       # Red-orange
                "falling_note_border": (0, 0, 0)          # Black
            }
            
            # Setup piano dimensions
            self.piano_start_y = self.screen_height - 180
            self.piano_start_x = 50
            self.white_key_width = 40
            self.white_key_height = 150
            self.black_key_width = 24
            self.black_key_height = 100
            
            # Setup note boundaries
            self.first_note = 36  # C2
            self.last_note = 96   # C7
            
            # Initialize classes
            self.music_theory = MusicTheory()
            self.midi_parser = AdvancedMIDIParser()
            
            # Load note sounds
            self._load_note_sounds()
            
            # Initialize MIDI input/output
            self._setup_midi_input()
            
            # Create key rectangles
            self._update_key_rect_map()
            
            # Initialize active notes set
            self.active_notes = set()
            
            # UI state tracking
            self.current_mode = self.settings["mode"]
            self.show_settings = False
            self.settings_scroll_offset = 0
            
            # Create UI controls for settings
            self._create_settings_controls()
            
            # Initialize start time and played notes
            self.start_time = None
            self.played_notes = set()
            
        except Exception as e:
            logging.exception("Failed to initialize Pygame modules.")
            # Optionally raise or handle more gracefully
            raise # Re-raise for now to make startup failure clear

    def is_black_key(self, note):
        """Determine if a note is a black key on the piano."""
        return note % 12 in [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#

    def _setup_midi_input(self):
        """Set up MIDI input device."""
        self.midi_input = None
        try:
            # Check available MIDI devices
            device_count = pygame.midi.get_count()
            if device_count == 0:
                logging.warning("No MIDI devices found.")
                return
            
            # Find the first input device
            for i in range(device_count):
                info = pygame.midi.get_device_info(i)
                if info[2] == 1:  # Is input device
                    logging.info(f"Using MIDI input device: {info[1]}")
                    self.midi_input = pygame.midi.Input(i)
                    break
            
            if self.midi_input is None:
                logging.warning("No MIDI input devices found.")
        except Exception as e:
            logging.exception("Error setting up MIDI input.")

    def play_note(self, note, velocity=127):
        """Play a piano note sound corresponding to the MIDI note number."""
        if note in self.note_sounds:
            # Set volume based on velocity (0-127)
            volume = min(1.0, velocity / 127.0)
            self.note_sounds[note].set_volume(volume)
            self.note_sounds[note].play()
        else:
            logging.warning(f"No sound available for note {note}")

    def _handle_midi_input(self):
        """Handle MIDI input from the connected device."""
        if not self.midi_input:
            return
        
        if self.midi_input.poll():
            midi_events = self.midi_input.read(10)  # Read up to 10 events
            for event in midi_events:
                data = event[0]
                timestamp = event[1]
                
                logging.debug(f"MIDI message received: {data}")
                
                status = data[0] & 0xF0  # Get the status byte (top 4 bits)
                channel = data[0] & 0x0F  # Get the channel (bottom 4 bits)
                
                # Handle Note On messages (key press)
                if status == 0x90:  # Note On
                    note = data[1]
                    velocity = data[2]
                    
                    if velocity > 0:
                        logging.debug(f"Note On: {note}, velocity: {velocity}")
                        
                        # Add the note to active notes
                        if note not in self.active_notes:
                            self.active_notes.add(note)
                            
                            # Play the corresponding sound
                            self.play_note(note, velocity)
                            
                            # Record when this note was played for learning mode
                            if self.current_mode == 'learning':
                                current_time = time.time() - self.start_time
                                self.played_notes.add(note)
                                logging.debug(f"Note {note} played at time {current_time:.2f}")
                    else:
                        # Note On with velocity 0 is equivalent to Note Off
                        logging.debug(f"Note Off: {note} (velocity 0)")
                        
                        if note in self.active_notes:
                            self.active_notes.remove(note)
                
                # Handle Note Off messages (key release)
                elif status == 0x80:  # Note Off
                    note = data[1]
                    logging.debug(f"Note Off: {note}")
                    
                    # Remove the note from active notes
                    if note in self.active_notes:
                        self.active_notes.remove(note)
    
        # Update the display based on active notes
        self._draw_piano(self.active_notes)
        pygame.display.update()

    def _draw_piano(self, active_notes=None):
        """Draw the piano keyboard."""
        if active_notes is None:
            active_notes = set(self.active_notes)  # Use currently played notes if no active_notes provided
        
        # First draw all white keys
        for note in range(self.first_note, self.last_note + 1):
            if not self.is_black_key(note):
                rect = self.key_rect_map.get(note)
                if rect:
                    # Highlight active white keys
                    if note in active_notes:
                        pygame.draw.rect(self.screen, self.colors["light_blue"], rect)
                        pygame.draw.rect(self.screen, self.colors["blue"], rect, 2)
                    else:
                        pygame.draw.rect(self.screen, self.colors["white"], rect)
                        pygame.draw.rect(self.screen, self.colors["black"], rect, 1)  # Border
                        
                    # Draw note name
                    note_name = AdvancedMIDIParser._get_note_name_static(note)
                    text_surf = self.stats_font.render(note_name, True, self.colors["black"])
                    text_rect = text_surf.get_rect(center=(rect.centerx, rect.bottom - 20))
                    self.screen.blit(text_surf, text_rect)
    
        # Then draw all black keys on top
        for note in range(self.first_note, self.last_note + 1):
            if self.is_black_key(note):
                rect = self.key_rect_map.get(note)
                if rect:
                    # Highlight active black keys
                    if note in active_notes:
                        pygame.draw.rect(self.screen, self.colors["blue"], rect)
                        pygame.draw.rect(self.screen, self.colors["light_blue"], rect, 2)
                    else:
                        pygame.draw.rect(self.screen, self.colors["black"], rect)
                        
                    # Draw note name on black keys
                    note_name = AdvancedMIDIParser._get_note_name_static(note)
                    text_surf = self.stats_font.render(note_name, True, self.colors["white"])
                    text_rect = text_surf.get_rect(center=(rect.centerx, rect.bottom - 20))
                    self.screen.blit(text_surf, text_rect)

    def _load_note_sounds(self):
        """Load piano note sound files from samples directory."""
        self.note_sounds = {}
        try:
            # Check if samples directory exists
            if not os.path.exists("samples"):
                logging.warning("Samples directory not found!")
                return
                
            for note in range(self.first_note, self.last_note + 1):
                note_name = AdvancedMIDIParser._get_note_name_static(note)
                try:
                    sound_path = f"samples/piano_{note_name}.wav"
                    if os.path.exists(sound_path):
                        self.note_sounds[note] = pygame.mixer.Sound(sound_path)
                        logging.debug(f"Loaded sound for {note_name}: {sound_path}")
                    else:
                        logging.warning(f"Sound file for {note_name} not found: {sound_path}")
                except Exception as e:
                    logging.warning(f"Error loading sound for {note_name}: {str(e)}")
        except Exception as e:
            logging.exception(f"Error loading note sounds: {str(e)}")

    def _update_key_rect_map(self):
        """Update the mapping of MIDI notes to screen rectangles."""
        self.key_rect_map = {}
        x = self.piano_start_x
        for note in range(self.first_note, self.last_note + 1):
            if not self.is_black_key(note):
                self.key_rect_map[note] = pygame.Rect(x, self.piano_start_y, self.white_key_width, self.white_key_height)
                x += self.white_key_width
        
        # Add black keys (must be done after white keys to know their positions)
        x = self.piano_start_x
        for note in range(self.first_note, self.last_note + 1):
            if not self.is_black_key(note):
                # Move to next white key position
                if note != self.last_note:
                    next_note = note + 1
                    if self.is_black_key(next_note):
                        # Position black key between white keys
                        self.key_rect_map[next_note] = pygame.Rect(
                            x + self.white_key_width - self.black_key_width // 2,
                            self.piano_start_y,
                            self.black_key_width,
                            self.black_key_height
                        )
                x += self.white_key_width
                
    def _setup_current_mode(self, mode, midi_file=None, learning_type=None, root_note=None, scale_chord_type=None):
        """Configure the application for the selected mode."""
        self.current_mode = mode
        self.learning_content = []
        self.falling_notes = None  # Reset falling notes
        self.played_notes = set()  # Reset played notes
        self.start_time = None  # Reset start time
        
        if mode == 'freestyle':
            logging.info("Setting up freestyle mode")
            self.midi_analysis = None
        
        elif mode == 'learning':
            logging.info(f"Setting up learning mode: {learning_type}")
            self.learning_content = self._generate_learning_sequence(
                type=learning_type, 
                root=root_note, 
                scale_type=scale_chord_type, 
                midi_file=midi_file
            )
            
            # Now that we have the learning content, initialize falling notes
            if self.learning_content:
                logging.info(f"Generated learning content with {len(self.learning_content)} notes")
                # Falling notes will be initialized in the render method
            else:
                logging.warning("No learning content was generated")
        
        elif mode == 'analysis_view':
            logging.info("Setting up analysis view mode")
            if midi_file:
                try:
                    self.midi_parser = AdvancedMIDIParser()
                    self.midi_analysis = self.midi_parser.parse_midi_file(midi_file)
                    self.analysis_report = self.midi_parser.generate_midi_analysis_report()
                except Exception as e:
                    logging.exception(f"Error parsing MIDI file: {midi_file}")
                    self.midi_analysis = None
                    self.analysis_report = f"Error analyzing file: {str(e)}"
            else:
                logging.warning("No MIDI file provided for analysis view")
                self.midi_analysis = None
                self.analysis_report = "No MIDI file provided."
                
    def _generate_learning_sequence(self, type="scale", root=60, scale_type="major", midi_file=None):
        """Generate a sequence of notes for learning mode."""
        if type == 'scale':
            return self.music_theory.generate_scale(root, scale_type)
        elif type == 'chord':
            return self.music_theory.generate_chord(root, scale_type)
        elif type == 'midi' and midi_file:
            try:
                # Log the MIDI file we're trying to parse
                logging.info(f"Parsing MIDI file: {midi_file}")
                
                parsed_notes = AdvancedMIDIParser.parse_midi_file(midi_file)
                
                # If parsing succeeded, log the number of notes
                if parsed_notes:
                    logging.info(f"Successfully parsed MIDI file. Found {len(parsed_notes)} notes.")
                    
                    # Log some sample notes for debugging
                    if len(parsed_notes) > 0:
                        sample_note = parsed_notes[0]
                        logging.info(f"Sample note: {sample_note}")
                    
                    # Add dummy test notes to ensure we always have visible notes
                    # This is for debugging only - add 10 evenly spaced notes
                    test_notes = []
                    for i in range(10):
                        test_note = {
                            'note': 60 + i % 12,  # C4 through B4
                            'start_sec': i * 2.0,  # Every 2 seconds
                            'duration_sec': 1.0,   # 1 second duration
                            'velocity': 100        # Medium velocity
                        }
                        test_notes.append(test_note)
                    
                    # Return both the parsed notes and our test notes
                    logging.info(f"Added 10 test notes to ensure visibility")
                    return parsed_notes + test_notes
                else:
                    logging.warning("Failed to parse MIDI file or no notes found")
                    # Return only test notes if parsing failed
                    return self._generate_test_notes()
            except Exception as e:
                logging.error(f"Error parsing MIDI file: {e}")
                return self._generate_test_notes()
        else:
            logging.error(f"Invalid learning type '{type}' or missing MIDI file")
            return []

    def _generate_test_notes(self):
        """Generate test notes for debugging."""
        logging.info("Generating test notes for debugging")
        test_notes = []
        for i in range(15):
            note = {
                'note': 60 + i % 24,      # C4 through B5 (two octaves)
                'start_sec': i,           # One per second
                'duration_sec': 0.8,      # 0.8 second duration
                'velocity': 100           # Medium velocity
            }
            test_notes.append(note)
        return test_notes

    def _setup_falling_notes(self):
        """Helper method to initialize falling notes for learning mode."""
        logging.info("Setting up falling notes for learning mode")
        target_y = self.screen_height - self.white_key_height - TARGET_LINE_Y_OFFSET
        self.falling_notes = []
        
        # Check if we have learning content
        if not self.learning_content:
            logging.warning("No learning content available to create falling notes")
            return
        
        # For MIDI files with timing information
        if self.settings["learning_type"] == 'midi' and isinstance(self.learning_content, list):
            # Create one note for each MIDI note in the learning content
            for note_info in self.learning_content:
                # Extract note data
                note = note_info['note']
                start_time = note_info['start_sec']
                duration = note_info['duration_sec']
                velocity = note_info.get('velocity', 127)
                
                # Create the falling note with properly set properties
                falling_note = FallingNote(
                    note=note,
                    start_time_sec=start_time + PREP_TIME_SEC,
                    duration_sec=max(0.1, duration),  # Ensure minimum duration for visibility
                    target_y=target_y,
                    screen_height=self.screen_height,
                    velocity=velocity
                )
                self.falling_notes.append(falling_note)
                
            logging.info(f"Created {len(self.falling_notes)} falling notes from MIDI file")
            
            # For debugging: log a sample of notes
            if len(self.falling_notes) > 0:
                sample_note = self.falling_notes[0]
                logging.info(f"Sample note - Number: {sample_note.note}, Start: {sample_note.start_time_sec}s, Duration: {sample_note.duration_sec}s")
        else:
            # For scales and chords (evenly spaced notes)
            current_time = 0.0
            spacing_time = 1.0  # Time between notes
            
            for note in self.learning_content:
                falling_note = FallingNote(
                    note=note,
                    start_time_sec=current_time + PREP_TIME_SEC,
                    duration_sec=0.5,  # Default duration for visibility
                    target_y=target_y,
                    screen_height=self.screen_height
                )
                self.falling_notes.append(falling_note)
                current_time += spacing_time
                
            logging.info(f"Created {len(self.falling_notes)} evenly spaced falling notes")
        
    def _render_learning_ui(self):
        """Render UI for learning mode."""
        # Draw title
        title_surf = self.title_font.render("Piano Trainer - Learning Mode", True, self.colors["black"])
        self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 20))
        
        # Make sure note colors are defined correctly
        self.colors["falling_note_upcoming"] = (50, 150, 255)  # Bright blue
        self.colors["falling_note_active"] = (255, 50, 50)     # Bright red
        self.colors["falling_note_hit"] = (50, 255, 50)        # Bright green
        self.colors["falling_note_missed"] = (200, 200, 200)   # Gray
        self.colors["falling_note_border"] = (0, 0, 0)         # Black
        
        # Start time for rendering
        current_time = time.time()
        if not hasattr(self, 'start_time') or self.start_time is None:
            self.start_time = current_time
            logging.info(f"Learning mode timer started at {self.start_time}")
        
        # Calculate time for drawing
        elapsed_time = current_time - self.start_time
        
        # Initialize/refresh falling notes if needed
        if not hasattr(self, 'falling_notes_ready') or not self.falling_notes_ready:
            self._setup_falling_notes()
            self.falling_notes_ready = True
            logging.info(f"Created {len(self.falling_notes)} falling notes in learning mode")
        
        # Draw target line
        target_y = self.screen_height - self.white_key_height - TARGET_LINE_Y_OFFSET
        pygame.draw.line(
            self.screen,
            self.colors["red"],
            (0, target_y),
            (self.screen_width, target_y),
            4  # Thicker line for better visibility
        )
        
        # Draw debug information
        debug_font = pygame.font.SysFont("Arial", 16)
        debug_text = [
            f"Notes: {len(self.falling_notes) if hasattr(self, 'falling_notes') else 0}",
            f"Time: {elapsed_time:.2f}s",
            f"Mode: {self.current_mode}/{self.settings.get('learning_type', 'unknown')}"
        ]
        y_pos = 50
        for text in debug_text:
            text_surf = debug_font.render(text, True, self.colors["black"])
            self.screen.blit(text_surf, (10, y_pos))
            y_pos += 20
        
        # Create some simple visual placeholders for debug purposes
        # Draw colored rectangles directly on the screen to show where notes would be
        note_count = len(self.falling_notes) if hasattr(self, 'falling_notes') else 0
        
        # Draw some debug rectangles to verify rendering is working
        debug_note_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255)   # Magenta
        ]
        
        for i in range(5):
            # Create debug rectangles at fixed positions
            rect = pygame.Rect(
                100 + (i * 50),   # Spaced 50 pixels apart
                target_y - 100,   # Above the target line
                30,               # Width
                60                # Height
            )
            # Draw with different colors
            pygame.draw.rect(
                self.screen,
                debug_note_colors[i % len(debug_note_colors)],
                rect
            )
            # Add a note name
            text_surf = self.note_font.render(f"Test {i+1}", True, self.colors["black"])
            self.screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery))
        
        # Now try to draw the actual falling notes
        active_notes = set()
        if note_count > 0:
            for i, note in enumerate(self.falling_notes):
                # Update position
                note.update(elapsed_time, self.key_rect_map)
                
                # Draw the note
                note.draw(self.screen, self.colors, self.note_font)
                
                # Also draw a fixed position debug version
                key_rect = self.key_rect_map.get(note.note)
                if key_rect and i < 10:  # Limit to 10 notes for debug display
                    # Draw a visual indicator
                    pygame.draw.rect(
                        self.screen,
                        self.colors["falling_note_upcoming"],
                        pygame.Rect(
                            key_rect.left, 
                            200 + (i * 30), 
                            key_rect.width, 
                            25
                        )
                    )
                    # Add the note name
                    name = AdvancedMIDIParser._get_note_name_static(note.note)
                    text_surf = self.note_font.render(name, True, self.colors["black"])
                    self.screen.blit(
                        text_surf, 
                        (key_rect.centerx - text_surf.get_width() // 2, 210 + (i * 30))
                    )
                
                # Track active notes
                if note.state == "active":
                    active_notes.add(note.note)
        else:
            # Show warning about no notes
            warning_text = "No notes available - check MIDI file!"
            warning_surf = self.note_font.render(warning_text, True, self.colors["red"])
            self.screen.blit(warning_surf, (self.screen_width // 2 - warning_surf.get_width() // 2, 150))
        
        # Process any MIDI input
        for note in self.falling_notes if hasattr(self, 'falling_notes') else []:
            if note.note in self.played_notes and note.state in ("active", "upcoming"):
                hit_time = int((current_time - self.start_time) * 1000)
                hit_result = note.check_hit(note.note, hit_time)
                if hit_result:
                    self.play_note(note.note, note.velocity)
        
        # Draw piano with active notes highlighted
        self._draw_piano(active_notes)
        
        # Display score
        hit_count = sum(1 for note in self.falling_notes if note.state == "hit") if hasattr(self, 'falling_notes') else 0
        score_text = f"Score: {hit_count}/{note_count}"
        score_surf = self.note_font.render(score_text, True, self.colors["black"])
        self.screen.blit(score_surf, (self.screen_width // 2 - score_surf.get_width() // 2, 90))
        
    def _render_analysis_ui(self):
        """Render UI for analysis view mode."""
        # This is a placeholder - analysis view would need more implementation
        title_surf = self.title_font.render("Piano Trainer - MIDI Analysis", True, self.colors["black"])
        self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 20))
        
        if hasattr(self, 'analysis_report'):
            # Display a portion of the analysis report
            lines = self.analysis_report.split('\n')[:10]  # First 10 lines
            for i, line in enumerate(lines):
                text_surf = self.stats_font.render(line, True, self.colors["black"])
                self.screen.blit(text_surf, (50, 70 + i * 20))
        
        # Draw piano
        self._draw_piano()

    def _cleanup(self):
        """Clean up resources and exit gracefully."""
        if hasattr(self, 'midi_input') and self.midi_input:
            self.midi_input.close()
        pygame.quit()
        logging.info("Piano Trainer closed.")

    def run(self, mode="freestyle", midi_file=None, difficulty="intermediate", learning_type="scale", root_note=60, scale_chord_type="major"):
        """Main application loop."""
        logging.info(f"Running in {mode} mode")
        
        # Initialize settings from arguments
        self.settings.update({
            "mode": mode,
            "midi_file": midi_file,
            "difficulty": difficulty,
            "learning_type": learning_type,
            "root_note": root_note,
            "scale_chord_type": scale_chord_type
        })
        
        # Setup based on mode and parameters
        self._setup_current_mode(
            mode=self.settings["mode"],
            midi_file=self.settings["midi_file"],
            learning_type=self.settings["learning_type"],
            root_note=self.settings["root_note"],
            scale_chord_type=self.settings["scale_chord_type"]
        )
        
        self.difficulty = self.settings["difficulty"]
        running = True
        clock = pygame.time.Clock()
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.show_settings:
                            self.show_settings = False
                        else:
                            running = False
                    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        # Toggle settings view with Ctrl+S
                        self.show_settings = not self.show_settings
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Handle mouse clicks for UI elements
                    if self.show_settings:
                        self._handle_settings_click(event.pos)
                        
            # Handle MIDI input (only if not in settings view)
            if not self.show_settings:
                self._handle_midi_input()
            
            # Render the appropriate UI based on mode
            self.screen.fill(self.colors["white"])
            
            if self.show_settings:
                self._render_settings_ui()
            elif self.settings["mode"] == "freestyle":
                self._render_freestyle_ui()
            elif self.settings["mode"] == "learning":
                self._render_learning_ui()
            elif self.settings["mode"] == "analysis_view":
                self._render_analysis_ui()
            
            # Update display
            pygame.display.flip()
            clock.tick(60)  # 60 FPS
        
        # Cleanup
        self._cleanup()

    def _render_freestyle_ui(self):
        """Render UI for freestyle mode."""
        # Draw title
        title_surf = self.title_font.render("Piano Trainer - Freestyle Mode", True, self.colors["black"])
        self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 20))
        
        # Draw instructions
        instructions = [
            "Play any notes on your MIDI keyboard",
            "Press ESC to exit",
            "Press Ctrl+S to access settings"
        ]
        
        for i, text in enumerate(instructions):
            text_surf = self.note_font.render(text, True, self.colors["black"])
            self.screen.blit(text_surf, (self.screen_width // 2 - text_surf.get_width() // 2, 70 + i * 30))
        
        # Draw piano
        self._draw_piano()
        
        # Draw active notes info
        if self.active_notes:
            notes_text = "Active Notes: " + ", ".join([AdvancedMIDIParser._get_note_name_static(note) for note in self.active_notes])
            notes_surf = self.stats_font.render(notes_text, True, self.colors["black"])
            self.screen.blit(notes_surf, (20, self.piano_start_y - 30))

    def _render_settings_ui(self):
        """Render the settings interface."""
        # Draw title
        title_surf = self.title_font.render("Piano Trainer - Settings", True, self.colors["black"])
        self.screen.blit(title_surf, (self.screen_width // 2 - title_surf.get_width() // 2, 20))
        
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((255, 255, 255, 220))  # White with 86% opacity
        self.screen.blit(overlay, (0, 0))
        
        # Draw instructions
        instructions = self.note_font.render("Change settings and press 'Apply Settings' to update", True, self.colors["black"])
        self.screen.blit(instructions, (self.screen_width // 2 - instructions.get_width() // 2, 60))
        
        # Store expanded dropdown for z-ordering (draw last)
        expanded_dropdown_key = None
        expanded_options = []
        
        # Draw each control and its label
        for key, control in self.settings_controls.items():
            # Draw label
            label_surf = self.stats_font.render(control["label"], True, self.colors["black"])
            self.screen.blit(label_surf, (50, control["rect"].y + 5))
            
            # Draw control based on type
            if control["type"] == "dropdown":
                # Draw dropdown background
                pygame.draw.rect(self.screen, self.colors["white"], control["rect"])
                pygame.draw.rect(self.screen, self.colors["black"], control["rect"], 2)
                
                # Draw current selection
                current_text = control["current"]
                if key == "midi_file" and current_text == "None":
                    current_text = "None (No MIDI file)"
                text_surf = self.stats_font.render(current_text, True, self.colors["black"])
                self.screen.blit(text_surf, (control["rect"].x + 10, control["rect"].y + 5))
                
                # Draw dropdown arrow
                arrow_points = [
                    (control["rect"].right - 20, control["rect"].y + 10),
                    (control["rect"].right - 10, control["rect"].y + 20),
                    (control["rect"].right - 30, control["rect"].y + 20)
                ]
                pygame.draw.polygon(self.screen, self.colors["black"], arrow_points)
                
                # If this dropdown is expanded, store it to draw last (on top)
                if hasattr(self, "expanded_dropdown") and self.expanded_dropdown == key:
                    expanded_dropdown_key = key
                    expanded_options = control["options"]
            
            elif control["type"] == "slider":
                # Draw slider track
                pygame.draw.rect(self.screen, self.colors["light_gray"], control["rect"])
                pygame.draw.rect(self.screen, self.colors["black"], control["rect"], 1)
                
                # Calculate handle position
                slider_range = control["max"] - control["min"]
                handle_pos = int(((control["value"] - control["min"]) / slider_range) * control["rect"].width)
                handle_rect = pygame.Rect(
                    control["rect"].x + handle_pos - 5,
                    control["rect"].y - 5,
                    10, 
                    control["rect"].height + 10
                )
                
                # Draw handle
                pygame.draw.rect(self.screen, self.colors["blue"], handle_rect)
                pygame.draw.rect(self.screen, self.colors["black"], handle_rect, 1)
                
                # Draw value text (include note name for root note)
                if key == "root_note":
                    value_text = f"{control['value']} ({AdvancedMIDIParser._get_note_name_static(control['value'])})"
                else:
                    value_text = str(control["value"])
                    
                value_surf = self.stats_font.render(value_text, True, self.colors["black"])
                self.screen.blit(value_surf, (control["rect"].right + 20, control["rect"].y + 5))
                
            elif control["type"] == "toggle":
                # Draw toggle background
                toggle_color = self.colors["green"] if control["value"] else self.colors["light_gray"]
                pygame.draw.rect(self.screen, toggle_color, control["rect"])
                pygame.draw.rect(self.screen, self.colors["black"], control["rect"], 1)
                
                # Draw toggle state text
                state_text = "ON" if control["value"] else "OFF"
                text_surf = self.stats_font.render(state_text, True, self.colors["black"])
                self.screen.blit(text_surf, (control["rect"].right + 20, control["rect"].y + 5))
                
            elif control["type"] == "text":
                # Draw text box
                pygame.draw.rect(self.screen, self.colors["white"], control["rect"])
                pygame.draw.rect(self.screen, self.colors["black"], control["rect"], 1)
                
                # Draw current text value
                text_surf = self.stats_font.render(control["value"] or "None", True, self.colors["black"])
                self.screen.blit(text_surf, (control["rect"].x + 10, control["rect"].y + 5))
                
                # Note: we don't handle text editing here for simplicity
                
            elif control["type"] == "button":
                # Draw button
                pygame.draw.rect(self.screen, self.colors["light_blue"], control["rect"])
                pygame.draw.rect(self.screen, self.colors["black"], control["rect"], 2)
                
                # Draw button text
                text_surf = self.stats_font.render(control["label"], True, self.colors["black"])
                text_rect = text_surf.get_rect(center=control["rect"].center)
                self.screen.blit(text_surf, text_rect)
        
        # Draw expanded dropdown options last (on top of everything)
        if expanded_dropdown_key:
            control = self.settings_controls[expanded_dropdown_key]
            option_height = 30
            dropdown_width = control["rect"].width
            
            # Create a floating panel for the dropdown that doesn't overlap other controls
            num_options = len(expanded_options)
            panel_height = num_options * option_height
            
            # Determine if dropdown should appear below or above
            space_below = self.screen_height - (control["rect"].y + control["rect"].height)
            if panel_height > space_below and control["rect"].y > panel_height:
                # Put panel above
                panel_y = control["rect"].y - panel_height
            else:
                # Put panel below
                panel_y = control["rect"].y + control["rect"].height
            
            # Create a background panel that encompasses all options
            panel_rect = pygame.Rect(control["rect"].x, panel_y, dropdown_width, panel_height)
            pygame.draw.rect(self.screen, self.colors["white"], panel_rect)
            pygame.draw.rect(self.screen, self.colors["black"], panel_rect, 2)
            
            # Draw each option
            for i, option in enumerate(expanded_options):
                option_rect = pygame.Rect(
                    control["rect"].x, 
                    panel_y + i * option_height,
                    dropdown_width, 
                    option_height
                )
                
                # Store the option rect for click detection
                if not hasattr(self, "dropdown_option_rects"):
                    self.dropdown_option_rects = {}
                if expanded_dropdown_key not in self.dropdown_option_rects:
                    self.dropdown_option_rects[expanded_dropdown_key] = {}
                self.dropdown_option_rects[expanded_dropdown_key][option] = option_rect
                
                # Highlight the selected option
                if option == control["current"]:
                    pygame.draw.rect(self.screen, self.colors["light_gray"], option_rect)
                
                # Draw option border
                pygame.draw.rect(self.screen, self.colors["black"], option_rect, 1)
                
                # Draw option text
                display_text = option
                if expanded_dropdown_key == "midi_file" and option == "None":
                    display_text = "None (No MIDI file)"
                text_surf = self.stats_font.render(display_text, True, self.colors["black"])
                self.screen.blit(text_surf, (option_rect.x + 10, option_rect.y + 5))

    def _handle_settings_click(self, pos):
        """Handle mouse click in settings UI."""
        # First check for dropdown options if a dropdown is expanded
        if hasattr(self, "expanded_dropdown") and self.expanded_dropdown and hasattr(self, "dropdown_option_rects"):
            dropdown_key = self.expanded_dropdown
            if dropdown_key in self.dropdown_option_rects:
                for option, option_rect in self.dropdown_option_rects[dropdown_key].items():
                    if option_rect.collidepoint(pos):
                        # Option was clicked, update the selection
                        self.settings_controls[dropdown_key]["current"] = option
                        
                        # Update actual settings
                        if dropdown_key == "midi_file" and option != "None":
                            # Convert the file name to a full path
                            midi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Midi_files", option)
                            self.settings[dropdown_key] = midi_path
                        elif dropdown_key == "midi_file" and option == "None":
                            self.settings[dropdown_key] = None
                        else:
                            self.settings[dropdown_key] = option
                            
                        # Close the dropdown
                        self.expanded_dropdown = None
                        self.dropdown_option_rects = {}
                        return  # Exit early as we've handled the click
                
                # If we clicked outside the dropdown options, close it
                self.expanded_dropdown = None
                self.dropdown_option_rects = {}
                return  # Exit early as we've handled the click
        
        # Then check regular controls
        for key, control in self.settings_controls.items():
            if control["rect"].collidepoint(pos):
                # Handle based on control type
                if control["type"] == "dropdown":
                    # Toggle dropdown expanded state
                    if not hasattr(self, "expanded_dropdown") or self.expanded_dropdown != key:
                        self.expanded_dropdown = key
                        # Clear any existing dropdown option rects
                        self.dropdown_option_rects = {}
                    else:
                        self.expanded_dropdown = None
                        self.dropdown_option_rects = {}
                            
                elif control["type"] == "slider":
                    # Handle slider drag - crude but effective
                    # Get value based on position in slider
                    if pygame.mouse.get_pressed()[0]:  # Left mouse button is held
                        slider_range = control["max"] - control["min"]
                        slider_width = control["rect"].width
                        rel_x = pos[0] - control["rect"].x
                        # Ensure within slider bounds
                        rel_x = max(0, min(rel_x, slider_width))
                        # Calculate value
                        value = control["min"] + int((rel_x / slider_width) * slider_range)
                        # Update control and settings
                        self.settings_controls[key]["value"] = value
                        self.settings[key] = value
                        
                elif control["type"] == "toggle":
                    # Toggle boolean value
                    new_value = not control["value"]
                    self.settings_controls[key]["value"] = new_value
                    self.settings[key] = new_value
                
                elif control["type"] == "button":
                    if key == "apply":
                        # Apply settings
                        self._apply_settings()
                    elif key == "close":
                        # Close settings view
                        self.show_settings = False
                        # Clear dropdown state
                        self.expanded_dropdown = None
                        self.dropdown_option_rects = {}
                        return  # Exit early as we've handled the click

    def _apply_settings(self):
        """Apply the current settings and reset the UI accordingly."""
        logging.info(f"Settings applied: {self.settings}")
        
        # Update the application mode based on settings
        self.current_mode = self.settings["mode"]
        
        # Update learning type if in learning mode
        if self.current_mode == "learning":
            self.learning_type = self.settings["learning_type"]
            
            # If learning from a MIDI file, load the file
            if self.learning_type == "midi" and "midi_file" in self.settings:
                self.midi_file_path = self.settings["midi_file"]
    
        # Reset UI and setup current mode with proper parameters
        self._setup_current_mode(
            mode=self.current_mode,
            learning_type=self.settings.get("learning_type"),
            midi_file=self.settings.get("midi_file"),
            root_note=self.settings.get("root_note"),
            scale_chord_type=self.settings.get("scale_chord_type")
        )
        
        # Hide settings after applying
        self.show_settings = False

    def _handle_midi_file_click(self, event):
        """Handle clicks on MIDI files in the settings menu."""
        if self.show_settings and self.midi_files:
            # We're in the settings menu and have MIDI files loaded
            if self.midi_file_rect.collidepoint(event.pos):
                # User clicked in the MIDI files area
                for i, (rect, midi_file) in enumerate(self.midi_file_rects):
                    if rect.collidepoint(event.pos):
                        self.settings["midi_file"] = midi_file
                        logging.info(f"Settings applied: {self.settings}")
                        # Explicitly set to learning mode with MIDI type
                        self.settings["mode"] = "learning"
                        self.settings["learning_type"] = "midi"
                        self.settings_midi_file = midi_file
                        self._apply_settings()
                        # Hide settings after selection
                        self.show_settings = False
                        return True
        return False

    def _handle_settings_event(self, event):
        """Handle events in the settings screen."""
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Check if a MIDI file was clicked
            if self.settings_current_tab == 'midi':
                for i, (rect, midi_file) in enumerate(self.midi_file_rects):
                    if rect.collidepoint(event.pos):
                        self.settings["midi_file"] = midi_file
                        logging.info(f"Settings applied: {self.settings}")
                        # Explicitly set to learning mode with MIDI type
                        self.settings["mode"] = "learning"
                        self.settings["learning_type"] = "midi"
                        self.settings_midi_file = midi_file
                        self._apply_settings()
                        return True
                    
            # Check if a tab was clicked
            for i, (rect, tab_name) in enumerate(self.tab_rects):
                if rect.collidepoint(event.pos):
                    self.settings_current_tab = tab_name
                    return True
                
            # Check for back button
            if self.back_button_rect.collidepoint(event.pos):
                self._apply_settings()
                self.show_settings = False
                return True

    def _create_settings_controls(self):
        """Create UI controls for settings."""
        # Create button and dropdown positions
        # Will be used in the settings UI
        self.settings_controls = {}
        
        # Mode selection
        self.settings_controls["mode"] = {
            "label": "Application Mode",
            "type": "dropdown",
            "options": ["freestyle", "learning", "analysis_view"],
            "current": self.settings["mode"],
            "rect": pygame.Rect(250, 100, 200, 30)
        }
        
        # MIDI file selection - Changed from text field to dropdown
        # Get list of MIDI files from the Midi_files directory
        midi_files = []
        midi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Midi_files")
        if os.path.exists(midi_dir):
            for file in os.listdir(midi_dir):
                if file.lower().endswith(('.mid', '.midi')):
                    midi_files.append(file)
            midi_files.sort()  # Sort alphabetically
        
        # Add a "None" option for no MIDI file
        midi_options = ["None"] + midi_files
        
        # Determine current selection
        current_midi = "None"
        if self.settings["midi_file"]:
            midi_basename = os.path.basename(self.settings["midi_file"])
            if midi_basename in midi_files:
                current_midi = midi_basename

        self.settings_controls["midi_file"] = {
            "label": "MIDI File",
            "type": "dropdown",
            "options": midi_options,
            "current": current_midi,
            "rect": pygame.Rect(250, 150, 300, 30)
        }
        
        # Learning type selection
        self.settings_controls["learning_type"] = {
            "label": "Learning Content",
            "type": "dropdown",
            "options": ["scale", "chord", "midi"],
            "current": self.settings["learning_type"],
            "rect": pygame.Rect(250, 200, 200, 30)
        }
        
        # Root note selection
        self.settings_controls["root_note"] = {
            "label": "Root Note",
            "type": "slider",
            "min": 36,
            "max": 84,
            "value": self.settings["root_note"],
            "rect": pygame.Rect(250, 250, 400, 30)
        }
        
        # Scale/chord type selection
        self.settings_controls["scale_chord_type"] = {
            "label": "Scale/Chord Type",
            "type": "dropdown",
            "options": list(MusicTheory.SCALE_INTERVALS.keys()) + list(MusicTheory.CHORD_INTERVALS.keys()),
            "current": self.settings["scale_chord_type"],
            "rect": pygame.Rect(250, 300, 200, 30)
        }
        
        # Difficulty selection
        self.settings_controls["difficulty"] = {
            "label": "Difficulty Level",
            "type": "dropdown",
            "options": ["easy", "intermediate", "hard"],
            "current": self.settings["difficulty"],
            "rect": pygame.Rect(250, 350, 200, 30)
        }
        
        # Log level selection
        self.settings_controls["log_level"] = {
            "label": "Log Level",
            "type": "dropdown",
            "options": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            "current": self.settings["log_level"],
            "rect": pygame.Rect(250, 400, 200, 30)
        }
        
        # Verbose toggle
        self.settings_controls["verbose"] = {
            "label": "Verbose Output",
            "type": "toggle",
            "value": self.settings["verbose"],
            "rect": pygame.Rect(250, 450, 30, 30)
        }
        
        # Apply button
        self.settings_controls["apply"] = {
            "label": "Apply Settings",
            "type": "button",
            "rect": pygame.Rect(250, 500, 150, 40)
        }
        
        # Close button
        self.settings_controls["close"] = {
            "label": "Close Settings",
            "type": "button",
            "rect": pygame.Rect(450, 500, 150, 40)
        }

# --- Main Execution Block ---
if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(
        description="Piano Trainer: Learn scales, chords, or play along with MIDI files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="freestyle",
        choices=["freestyle", "learning", "analysis_view"],
        help="Application mode: freestyle, learning, or analysis_view.",
    )
    parser.add_argument(
        "--midi",
        type=str,
        default=None,
        help="Path to a MIDI file to load (used in learning mode with --learn midi or analysis_view).",
    )
    parser.add_argument(
        "--learn",
        type=str,
        default="scale",
        choices=["scale", "chord", "midi"],
        help="Learning content type (only used in learning mode).",
    )
    parser.add_argument(
        "--root",
        type=int,
        default=60,
        help="Root MIDI note number for scales/chords (e.g., 60=C4).",
    )
    parser.add_argument(
        "--type",
        type=str,
        default="major",
        help="Scale or chord type (e.g., 'major', 'min7', 'chromatic').",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="intermediate",
        choices=["easy", "intermediate", "hard"],
        help="Difficulty level for learning mode.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (sets log level to DEBUG).",
    )

    args = parser.parse_args()

    # Logging Setup
    log_level_str = "DEBUG" if args.verbose else args.log
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    log_format = "%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"
    log_filename = "piano_trainer.log"
    logging.basicConfig(
        level=log_level,
        format=log_format,
        filename=log_filename,
        filemode="w",  # Overwrite log file each time
    )
    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)

    logging.info("========== Application Starting ==========")
    logging.info(f"Command line arguments: {vars(args)}")

    # Instantiate the UI class directly
    try:
        trainer = EnhancedPianoTrainerUI()
        # Call the run method with parameters mapped from args
        trainer.run(
            mode=args.mode,
            difficulty=args.difficulty,
            learning_type=args.learn,
            root_note=args.root,
            scale_chord_type=args.type,
            midi_file=args.midi # Pass the file path, run() or setup will handle loading
        )
    except Exception as e:
        logging.exception("Unhandled exception during initialization or run.")
        print(f"An error occurred: {e}", file=sys.stderr)
    finally:
        logging.info("========== Application Finished ==========")

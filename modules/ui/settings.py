"""
Settings UI module for the Comprehensive Piano Application
Handles the settings menu and user preferences
"""
import pygame
from typing import Dict, List, Tuple, Optional, Any, Callable

class SettingsUI:
    """Handles the settings interface and user preferences."""
    
    def __init__(self):
        """Initialize the settings UI."""
        # Default settings
        self.settings = {
            "volume": 0.7,
            "key_range": {
                "first_note": 21,  # A0
                "total_keys": 88,  # Full piano
            },
            "show_note_names": True,
            "show_octave_markers": True,
            "difficulty": "intermediate",  # easy, intermediate, hard
            "audio_mode": "samples",  # samples or synth
            "midi_device": None,
            "reverb_amount": 0.2,
            "falling_speed": 150,  # Pixels per second
            "hit_window": 200,  # Milliseconds
            "prep_time": 3.0,  # Seconds
            "show_performance_stats": True,
        }
        
        # UI elements
        self.active = False
        self.controls = {}
        self.screen = None
        self.font = None
        self.title_font = None
        
        # Settings panel dimensions
        self.panel_rect = None
        self.settings_changed_callback = None
    
    def initialize(self, screen, font=None, title_font=None):
        """Initialize the settings UI with pygame screen and fonts.
        
        Args:
            screen: Pygame screen surface
            font: Main font for UI text
            title_font: Font for section titles
        """
        self.screen = screen
        self.font = font or pygame.font.SysFont("Arial", 24)
        self.title_font = title_font or pygame.font.SysFont("Arial", 32, bold=True)
        
        # Create settings panel centered on screen
        width, height = screen.get_size()
        panel_width = min(600, width - 100)
        panel_height = min(500, height - 100)
        
        self.panel_rect = pygame.Rect(
            (width - panel_width) // 2,
            (height - panel_height) // 2,
            panel_width,
            panel_height
        )
        
        # Create UI controls
        self._build_controls()
    
    def _build_controls(self):
        """Build all UI controls for settings."""
        if not self.panel_rect:
            return
            
        # Control spacing
        margin = 20
        section_margin = 40
        control_height = 30
        
        # Current Y position for layout
        y = self.panel_rect.y + margin
        
        # Volume slider
        self._add_slider(
            "volume", 
            "Volume", 
            self.settings["volume"], 
            0.0, 1.0, 
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{int(v * 100)}%"
        )
        y += control_height + margin
        
        # Audio settings section
        y += section_margin
        self._add_section_title("Audio Settings", y)
        y += control_height + margin
        
        # Audio mode toggle
        self._add_toggle(
            "audio_mode_samples",
            "Use Sample-based Audio",
            self.settings["audio_mode"] == "samples",
            x=self.panel_rect.x + margin,
            y=y
        )
        y += control_height + margin
        
        # Reverb slider
        self._add_slider(
            "reverb_amount", 
            "Reverb Amount", 
            self.settings["reverb_amount"], 
            0.0, 0.8, 
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{int(v * 100)}%"
        )
        y += control_height + margin
        
        # Display settings section
        y += section_margin
        self._add_section_title("Display Settings", y)
        y += control_height + margin
        
        # Show note names toggle
        self._add_toggle(
            "show_note_names",
            "Show Note Names",
            self.settings["show_note_names"],
            x=self.panel_rect.x + margin,
            y=y
        )
        y += control_height + margin
        
        # Show octave markers toggle
        self._add_toggle(
            "show_octave_markers",
            "Show Octave Markers",
            self.settings["show_octave_markers"],
            x=self.panel_rect.x + margin,
            y=y
        )
        y += control_height + margin
        
        # Learning mode section
        y += section_margin
        self._add_section_title("Learning Mode", y)
        y += control_height + margin
        
        # Difficulty dropdown
        self._add_dropdown(
            "difficulty",
            "Difficulty",
            self.settings["difficulty"],
            ["easy", "intermediate", "hard"],
            x=self.panel_rect.x + margin,
            y=y,
            width=300
        )
        y += control_height + margin
        
        # Falling speed slider
        self._add_slider(
            "falling_speed", 
            "Note Speed", 
            self.settings["falling_speed"], 
            50, 300, 
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{int(v)} px/s"
        )
        y += control_height + margin
        
        # Hit window slider
        self._add_slider(
            "hit_window", 
            "Timing Window", 
            self.settings["hit_window"], 
            50, 500, 
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{int(v)} ms"
        )
        y += control_height + margin
        
        # Show performance stats toggle
        self._add_toggle(
            "show_performance_stats",
            "Show Performance Statistics",
            self.settings["show_performance_stats"],
            x=self.panel_rect.x + margin,
            y=y
        )
        y += control_height + margin
        
        # Close button at the bottom
        button_width = 120
        self._add_button(
            "save_settings",
            "Save",
            x=self.panel_rect.x + self.panel_rect.width - button_width - margin,
            y=self.panel_rect.y + self.panel_rect.height - control_height - margin,
            width=button_width
        )
        
        # Cancel button
        self._add_button(
            "cancel_settings",
            "Cancel",
            x=self.panel_rect.x + self.panel_rect.width - 2*button_width - 2*margin,
            y=self.panel_rect.y + self.panel_rect.height - control_height - margin,
            width=button_width
        )
    
    def _add_section_title(self, title, y):
        """Add a section title to the settings UI.
        
        Args:
            title (str): Section title
            y (int): Y-coordinate
        """
        self.controls[f"section_{title}"] = {
            "type": "title",
            "text": title,
            "rect": pygame.Rect(
                self.panel_rect.x + 20,
                y,
                self.panel_rect.width - 40,
                30
            )
        }
    
    def _add_slider(self, key, label, value, min_value, max_value, x, y, width=300, formatter=str):
        """Add a slider control to the settings UI.
        
        Args:
            key (str): Setting key
            label (str): Control label
            value (float): Current value
            min_value (float): Minimum value
            max_value (float): Maximum value
            x (int): X-coordinate
            y (int): Y-coordinate
            width (int): Control width
            formatter (callable): Function to format value as string
        """
        self.controls[key] = {
            "type": "slider",
            "label": label,
            "value": value,
            "min_value": min_value,
            "max_value": max_value,
            "formatter": formatter,
            "rect": pygame.Rect(x, y, width, 30),
            "handle_rect": pygame.Rect(
                x + int((value - min_value) / (max_value - min_value) * width),
                y,
                10,
                30
            ),
            "dragging": False
        }
    
    def _add_toggle(self, key, label, value, x, y):
        """Add a toggle control to the settings UI.
        
        Args:
            key (str): Setting key
            label (str): Control label
            value (bool): Current value
            x (int): X-coordinate
            y (int): Y-coordinate
        """
        self.controls[key] = {
            "type": "toggle",
            "label": label,
            "value": value,
            "rect": pygame.Rect(x, y, 30, 30)
        }
    
    def _add_dropdown(self, key, label, value, options, x, y, width=300):
        """Add a dropdown control to the settings UI.
        
        Args:
            key (str): Setting key
            label (str): Control label
            value (str): Current value
            options (List[str]): Available options
            x (int): X-coordinate
            y (int): Y-coordinate
            width (int): Control width
        """
        self.controls[key] = {
            "type": "dropdown",
            "label": label,
            "value": value,
            "options": options,
            "expanded": False,
            "rect": pygame.Rect(x, y, width, 30),
            "option_rects": [
                pygame.Rect(x, y + 30 + i*30, width, 30)
                for i in range(len(options))
            ]
        }
    
    def _add_button(self, key, label, x, y, width=120):
        """Add a button control to the settings UI.
        
        Args:
            key (str): Button key
            label (str): Button label
            x (int): X-coordinate
            y (int): Y-coordinate
            width (int): Button width
        """
        self.controls[key] = {
            "type": "button",
            "label": label,
            "rect": pygame.Rect(x, y, width, 30)
        }
    
    def draw(self):
        """Draw the settings UI if active."""
        if not self.active or not self.screen:
            return
            
        # Draw panel background
        pygame.draw.rect(
            self.screen,
            (240, 240, 240),
            self.panel_rect
        )
        pygame.draw.rect(
            self.screen,
            (0, 0, 0),
            self.panel_rect,
            2
        )
        
        # Draw title
        title_text = self.title_font.render("Settings", True, (0, 0, 0))
        self.screen.blit(
            title_text,
            (
                self.panel_rect.x + (self.panel_rect.width - title_text.get_width()) // 2,
                self.panel_rect.y + 10
            )
        )
        
        # Draw controls
        for key, control in self.controls.items():
            control_type = control["type"]
            
            if control_type == "title":
                # Draw section title
                text = self.title_font.render(control["text"], True, (50, 50, 50))
                self.screen.blit(text, (control["rect"].x, control["rect"].y))
                
                # Draw separator line
                pygame.draw.line(
                    self.screen,
                    (200, 200, 200),
                    (control["rect"].x, control["rect"].y + text.get_height() + 5),
                    (control["rect"].x + control["rect"].width, control["rect"].y + text.get_height() + 5),
                    2
                )
                
            elif control_type == "slider":
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(label_text, (control["rect"].x, control["rect"].y - 25))
                
                # Draw slider track
                pygame.draw.rect(
                    self.screen,
                    (200, 200, 200),
                    (control["rect"].x, control["rect"].y + 13, control["rect"].width, 4)
                )
                
                # Draw slider handle
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 200),
                    control["handle_rect"]
                )
                
                # Draw value
                value_text = self.font.render(
                    control["formatter"](control["value"]), 
                    True, 
                    (0, 0, 0)
                )
                self.screen.blit(
                    value_text,
                    (control["rect"].x + control["rect"].width + 10, control["rect"].y)
                )
                
            elif control_type == "toggle":
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(label_text, (control["rect"].x + 40, control["rect"].y + 5))
                
                # Draw toggle box
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 200) if control["value"] else (200, 200, 200),
                    control["rect"]
                )
                
                # Draw checkmark if enabled
                if control["value"]:
                    # Draw checkmark
                    points = [
                        (control["rect"].x + 7, control["rect"].y + 15),
                        (control["rect"].x + 13, control["rect"].y + 21),
                        (control["rect"].x + 23, control["rect"].y + 9)
                    ]
                    pygame.draw.lines(
                        self.screen,
                        (255, 255, 255),
                        False,
                        points,
                        2
                    )
                
            elif control_type == "dropdown":
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(label_text, (control["rect"].x, control["rect"].y - 25))
                
                # Draw dropdown box
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    control["rect"]
                )
                pygame.draw.rect(
                    self.screen,
                    (0, 0, 0),
                    control["rect"],
                    1
                )
                
                # Draw selected value
                value_text = self.font.render(control["value"], True, (0, 0, 0))
                self.screen.blit(
                    value_text,
                    (control["rect"].x + 10, control["rect"].y + 5)
                )
                
                # Draw dropdown arrow
                arrow_points = [
                    (control["rect"].x + control["rect"].width - 20, control["rect"].y + 10),
                    (control["rect"].x + control["rect"].width - 10, control["rect"].y + 10),
                    (control["rect"].x + control["rect"].width - 15, control["rect"].y + 20)
                ]
                pygame.draw.polygon(
                    self.screen,
                    (0, 0, 0),
                    arrow_points
                )
                
                # If expanded, draw options
                if control["expanded"]:
                    options_height = len(control["options"]) * 30
                    # Draw options background
                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 255),
                        (control["rect"].x, control["rect"].y + 30, control["rect"].width, options_height)
                    )
                    pygame.draw.rect(
                        self.screen,
                        (0, 0, 0),
                        (control["rect"].x, control["rect"].y + 30, control["rect"].width, options_height),
                        1
                    )
                    
                    # Draw each option
                    for i, option in enumerate(control["options"]):
                        option_rect = control["option_rects"][i]
                        # Highlight if hovered
                        if option == control["value"]:
                            pygame.draw.rect(
                                self.screen,
                                (220, 220, 255),
                                option_rect
                            )
                        
                        # Draw option text
                        option_text = self.font.render(option, True, (0, 0, 0))
                        self.screen.blit(
                            option_text,
                            (option_rect.x + 10, option_rect.y + 5)
                        )
                
            elif control_type == "button":
                # Draw button
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 200),
                    control["rect"]
                )
                
                # Draw label
                label_text = self.font.render(control["label"], True, (255, 255, 255))
                self.screen.blit(
                    label_text,
                    (
                        control["rect"].x + (control["rect"].width - label_text.get_width()) // 2,
                        control["rect"].y + (control["rect"].height - label_text.get_height()) // 2
                    )
                )
    
    def handle_event(self, event):
        """Handle pygame events for the settings UI.
        
        Args:
            event: Pygame event
            
        Returns:
            bool: True if the event was handled, False otherwise
        """
        if not self.active:
            return False
            
        # Mouse click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            # Check each control
            for key, control in self.controls.items():
                control_type = control["type"]
                
                if control_type == "slider" and control["rect"].collidepoint(pos):
                    # Start dragging slider
                    control["dragging"] = True
                    self._update_slider_value(key, pos[0])
                    return True
                    
                elif control_type == "toggle" and control["rect"].collidepoint(pos):
                    # Toggle value
                    control["value"] = not control["value"]
                    self._apply_toggle_setting(key)
                    return True
                    
                elif control_type == "dropdown" and control["rect"].collidepoint(pos):
                    # Toggle dropdown expansion
                    control["expanded"] = not control["expanded"]
                    return True
                    
                elif control_type == "dropdown" and control["expanded"]:
                    # Check if clicked on an option
                    for i, option_rect in enumerate(control["option_rects"]):
                        if option_rect.collidepoint(pos):
                            control["value"] = control["options"][i]
                            control["expanded"] = False
                            self._apply_dropdown_setting(key)
                            return True
                    
                elif control_type == "button" and control["rect"].collidepoint(pos):
                    # Handle button click
                    self._handle_button_click(key)
                    return True
            
            # If clicked outside any control, but on the panel, eat the event
            if self.panel_rect.collidepoint(pos):
                return True
                
            # If clicked outside the panel, close settings
            self.active = False
            return True
            
        # Mouse movement with button down
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            pos = event.pos
            
            # Update dragging sliders
            for key, control in self.controls.items():
                if control["type"] == "slider" and control["dragging"]:
                    self._update_slider_value(key, pos[0])
                    return True
            
        # Mouse button release
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # Stop dragging all sliders
            for key, control in self.controls.items():
                if control["type"] == "slider" and control["dragging"]:
                    control["dragging"] = False
                    self._apply_slider_setting(key)
            
        # Keypress
        elif event.type == pygame.KEYDOWN:
            # ESC to close settings
            if event.key == pygame.K_ESCAPE:
                self.active = False
                return True
        
        return False
    
    def _update_slider_value(self, key, x_pos):
        """Update a slider value based on mouse position.
        
        Args:
            key (str): Slider key
            x_pos (int): Mouse X-coordinate
        """
        control = self.controls[key]
        rect = control["rect"]
        
        # Clamp position to slider track
        x_pos = max(rect.x, min(rect.x + rect.width, x_pos))
        
        # Calculate value
        min_value = control["min_value"]
        max_value = control["max_value"]
        value_range = max_value - min_value
        
        normalized_pos = (x_pos - rect.x) / rect.width
        value = min_value + (normalized_pos * value_range)
        
        # Update control
        control["value"] = value
        control["handle_rect"].x = x_pos - control["handle_rect"].width // 2
    
    def _apply_slider_setting(self, key):
        """Apply a slider setting value.
        
        Args:
            key (str): Slider key
        """
        control = self.controls[key]
        
        if key == "volume":
            self.settings["volume"] = control["value"]
        elif key == "reverb_amount":
            self.settings["reverb_amount"] = control["value"]
        elif key == "falling_speed":
            self.settings["falling_speed"] = control["value"]
        elif key == "hit_window":
            self.settings["hit_window"] = control["value"]
            
        # Notify about changed settings
        if self.settings_changed_callback:
            self.settings_changed_callback()
    
    def _apply_toggle_setting(self, key):
        """Apply a toggle setting value.
        
        Args:
            key (str): Toggle key
        """
        control = self.controls[key]
        
        if key == "show_note_names":
            self.settings["show_note_names"] = control["value"]
        elif key == "show_octave_markers":
            self.settings["show_octave_markers"] = control["value"]
        elif key == "show_performance_stats":
            self.settings["show_performance_stats"] = control["value"]
        elif key == "audio_mode_samples":
            self.settings["audio_mode"] = "samples" if control["value"] else "synth"
            
        # Notify about changed settings
        if self.settings_changed_callback:
            self.settings_changed_callback()
    
    def _apply_dropdown_setting(self, key):
        """Apply a dropdown setting value.
        
        Args:
            key (str): Dropdown key
        """
        control = self.controls[key]
        
        if key == "difficulty":
            self.settings["difficulty"] = control["value"]
            
        # Notify about changed settings
        if self.settings_changed_callback:
            self.settings_changed_callback()
    
    def _handle_button_click(self, key):
        """Handle a button click.
        
        Args:
            key (str): Button key
        """
        if key == "save_settings":
            # Close settings
            self.active = False
            
            # Apply all settings
            if self.settings_changed_callback:
                self.settings_changed_callback()
                
        elif key == "cancel_settings":
            # Close settings without saving
            self.active = False
            
            # Rebuild controls to reset values
            self._build_controls()
    
    def set_settings_changed_callback(self, callback):
        """Set a callback for when settings are changed.
        
        Args:
            callback (callable): Function to call when settings change
        """
        self.settings_changed_callback = callback
    
    def show(self):
        """Show the settings UI."""
        self.active = True
    
    def hide(self):
        """Hide the settings UI."""
        self.active = False
    
    def is_visible(self):
        """Check if the settings UI is visible.
        
        Returns:
            bool: True if the settings UI is visible
        """
        return self.active
    
    def get_setting(self, key):
        """Get a setting value.
        
        Args:
            key (str): Setting key
            
        Returns:
            Any: Setting value
        """
        return self.settings.get(key)
    
    def set_setting(self, key, value):
        """Set a setting value.
        
        Args:
            key (str): Setting key
            value: Setting value
        """
        self.settings[key] = value
        
        # Update control if it exists
        if key in self.controls:
            self.controls[key]["value"] = value
        
        # Special case for audio mode toggle
        if key == "audio_mode" and "audio_mode_samples" in self.controls:
            self.controls["audio_mode_samples"]["value"] = (value == "samples")

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
            "learning_visualization": "both",  # "falling", "highlight", or "both"
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
        
        # Top title for settings
        font_title = pygame.font.SysFont("Arial", 36, bold=True)
        title_surface = font_title.render("Settings", True, (0, 0, 0))
        self.controls["title"] = {
            "type": "label",
            "rect": pygame.Rect(
                self.panel_rect.centerx - title_surface.get_width() // 2, 
                y, 
                title_surface.get_width(), 
                title_surface.get_height()
            ),
            "surface": title_surface
        }
        y += title_surface.get_height() + margin
        
        # Learning Mode Settings
        # ----------------------
        self._add_section_title("Learning Mode Settings", y)
        y += control_height + margin
        
        # Learning visualization dropdown
        self._add_dropdown(
            "learning_visualization",
            "Learning Visualization",
            self.settings["learning_visualization"],
            [
                ("falling", "Falling Notes Only"), 
                ("highlight", "Highlighted Keys Only"), 
                ("both", "Both Combined")
            ],
            x=self.panel_rect.x + margin,
            y=y,
            width=300
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
        
        # Falling speed slider
        self._add_slider(
            "falling_speed",
            "Falling Notes Speed",
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
            "Hit Window",
            self.settings["hit_window"],
            50, 500,
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{int(v)} ms"
        )
        y += control_height + margin
        
        # Preparation time slider
        self._add_slider(
            "prep_time",
            "Preparation Time",
            self.settings["prep_time"],
            1.0, 5.0,
            x=self.panel_rect.x + margin,
            y=y,
            width=300,
            formatter=lambda v: f"{v:.1f} sec"
        )
        y += control_height + section_margin
        
        # Audio Settings
        # -------------
        self._add_section_title("Audio Settings", y)
        y += control_height + margin
        
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
        y += control_height + section_margin
        
        # Display Settings
        # ---------------
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
        
        # Difficulty dropdown
        self._add_dropdown(
            "difficulty",
            "Difficulty Level",
            self.settings["difficulty"],
            [
                ("easy", "Easy"), 
                ("intermediate", "Intermediate"), 
                ("hard", "Hard")
            ],
            x=self.panel_rect.x + margin,
            y=y,
            width=300
        )
        y += control_height + section_margin
        
        # Buttons
        # -------
        self._add_button("save_settings", "Save", self.panel_rect.centerx - 130, y)
        self._add_button("cancel_settings", "Cancel", self.panel_rect.centerx + 10, y)
    
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
            (240, 240, 245),
            self.panel_rect
        )
        pygame.draw.rect(
            self.screen,
            (100, 100, 100),
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
            control_type = control.get("type", "")
            
            if control_type == "slider":
                # Draw slider background
                pygame.draw.rect(
                    self.screen,
                    (200, 200, 200),
                    control["rect"]
                )
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    control["rect"],
                    1
                )
                
                # Draw slider handle
                handle_x = int(control["rect"].x + (control["value"] - control["min_value"]) / 
                              (control["max_value"] - control["min_value"]) * control["rect"].width)
                handle_rect = pygame.Rect(
                    handle_x - 5, 
                    control["rect"].y - 5, 
                    10, 
                    control["rect"].height + 10
                )
                pygame.draw.rect(
                    self.screen,
                    (50, 100, 200),
                    handle_rect
                )
                pygame.draw.rect(
                    self.screen,
                    (20, 50, 100),
                    handle_rect,
                    1
                )
                
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(
                    label_text, 
                    (
                        control["rect"].x, 
                        control["rect"].y - label_text.get_height() - 5
                    )
                )
                
                # Draw value
                if "formatter" in control:
                    value_text = control["formatter"](control["value"])
                else:
                    value_text = str(control["value"])
                    
                value_surface = self.font.render(value_text, True, (0, 0, 0))
                self.screen.blit(
                    value_surface, 
                    (
                        control["rect"].x + control["rect"].width + 10, 
                        control["rect"].y + (control["rect"].height - value_surface.get_height()) // 2
                    )
                )
                
            elif control_type == "dropdown":
                # Draw dropdown background
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 255),
                    control["rect"]
                )
                pygame.draw.rect(
                    self.screen,
                    (100, 100, 100),
                    control["rect"],
                    1
                )
                
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(
                    label_text, 
                    (
                        control["rect"].x, 
                        control["rect"].y - label_text.get_height() - 5
                    )
                )
                
                # Get the current value to display
                current_value = control["value"]
                display_text = current_value  # Default

                # If options are tuples (value, display_text), find the display text for the current value
                for option in control["options"]:
                    if isinstance(option, tuple) and len(option) == 2:
                        if option[0] == current_value:
                            display_text = option[1]
                            break
                
                # Draw current value
                value_text = self.font.render(display_text, True, (0, 0, 0))
                self.screen.blit(
                    value_text, 
                    (
                        control["rect"].x + 10, 
                        control["rect"].y + (control["rect"].height - value_text.get_height()) // 2
                    )
                )
                
                # Draw dropdown arrow
                arrow_rect = pygame.Rect(
                    control["rect"].x + control["rect"].width - 20,
                    control["rect"].y + 5,
                    15,
                    control["rect"].height - 10
                )
                pygame.draw.polygon(
                    self.screen,
                    (50, 50, 50),
                    [
                        (arrow_rect.x, arrow_rect.y),
                        (arrow_rect.x + arrow_rect.width, arrow_rect.y),
                        (arrow_rect.x + arrow_rect.width // 2, arrow_rect.y + arrow_rect.height)
                    ]
                )
                
                # Draw dropdown list if open
                if control.get("open", False):
                    # Calculate dropdown list height
                    list_height = len(control["options"]) * 30
                    list_rect = pygame.Rect(
                        control["rect"].x,
                        control["rect"].y + control["rect"].height,
                        control["rect"].width,
                        list_height
                    )
                    
                    # Draw list background
                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 255),
                        list_rect
                    )
                    pygame.draw.rect(
                        self.screen,
                        (100, 100, 100),
                        list_rect,
                        1
                    )
                    
                    # Draw options
                    for i, option in enumerate(control["options"]):
                        option_rect = pygame.Rect(
                            list_rect.x,
                            list_rect.y + i * 30,
                            list_rect.width,
                            30
                        )
                        
                        # Highlight selected option
                        option_value = option[0] if isinstance(option, tuple) and len(option) == 2 else option
                        option_display = option[1] if isinstance(option, tuple) and len(option) == 2 else option
                        
                        if option_value == control["value"]:
                            pygame.draw.rect(
                                self.screen,
                                (200, 220, 255),
                                option_rect
                            )
                            
                        # Draw option text
                        option_text = self.font.render(option_display, True, (0, 0, 0))
                        self.screen.blit(
                            option_text,
                            (
                                option_rect.x + 10,
                                option_rect.y + (option_rect.height - option_text.get_height()) // 2
                            )
                        )
                
            elif control_type == "toggle":
                # Draw toggle box
                pygame.draw.rect(
                    self.screen,
                    (50, 50, 200) if control["value"] else (200, 200, 200),
                    control["rect"]
                )
                
                # Draw label
                label_text = self.font.render(control["label"], True, (0, 0, 0))
                self.screen.blit(
                    label_text,
                    (
                        control["rect"].x + 40,
                        control["rect"].y + 5
                    )
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
                
            elif control_type == "label":
                self.screen.blit(control["surface"], control["rect"])
    
    def handle_event(self, event):
        """Handle pygame events for the settings UI.
        
        Args:
            event: Pygame event
            
        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            # Check if clicked on a control
            for key, control in self.controls.items():
                control_type = control.get("type", "")
                
                if control_type == "slider" and control["rect"].collidepoint(pos):
                    # Start dragging slider
                    control["dragging"] = True
                    # Update slider value immediately
                    self._update_slider_value(key, pos[0])
                    return True
                    
                elif control_type == "toggle" and control["rect"].collidepoint(pos):
                    # Toggle value
                    control["value"] = not control["value"]
                    self._apply_toggle_setting(key)
                    return True
                    
                elif control_type == "dropdown" and control["rect"].collidepoint(pos):
                    # Toggle dropdown expansion
                    control["open"] = not control.get("open", False)
                    return True
                    
                elif control_type == "dropdown" and control.get("open", False):
                    # Check if clicked on an option
                    # Calculate dropdown list height
                    list_height = len(control["options"]) * 30
                    list_rect = pygame.Rect(
                        control["rect"].x,
                        control["rect"].y + control["rect"].height,
                        control["rect"].width,
                        list_height
                    )
                    
                    if list_rect.collidepoint(pos):
                        # Calculate which option was clicked
                        option_index = (pos[1] - list_rect.y) // 30
                        if 0 <= option_index < len(control["options"]):
                            option = control["options"][option_index]
                            # If option is a tuple, use first element as value
                            if isinstance(option, tuple) and len(option) == 2:
                                control["value"] = option[0]
                            else:
                                control["value"] = option
                                
                            control["open"] = False
                            self._apply_dropdown_setting(key)
                            return True
                    else:
                        # Close dropdown if clicked outside
                        control["open"] = False
                    
                elif control_type == "button" and control["rect"].collidepoint(pos):
                    # Handle button click
                    if key == "save_settings":
                        self._save_settings()
                        self.hide()
                    elif key == "cancel_settings":
                        self._load_settings()  # Restore original settings
                        self.hide()
                    return True
            
            # If clicked outside any control, but on the panel, eat the event
            if self.panel_rect.collidepoint(pos):
                return True
                
            # If clicked outside the panel, close settings
            self.active = False
            return True
            
        # Mouse movement with button down
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            pos = pygame.mouse.get_pos()
            
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
        elif key == "prep_time":
            self.settings["prep_time"] = control["value"]
            
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
        elif key == "learning_visualization":
            self.settings["learning_visualization"] = control["value"]
            
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

    def _save_settings(self):
        """Save settings and notify the callback."""
        # Since we've been updating self.settings as changes are made,
        # we just need to notify the callback
        if self.settings_changed_callback:
            self.settings_changed_callback(self.settings)
            
    def _load_settings(self):
        """Reload settings from the original values."""
        # Reset local settings to their original values
        # Note: This assumes that settings_changed_callback can provide the original settings
        if self.settings_changed_callback:
            # Trigger a reload from the parent component
            self.settings_changed_callback(None, reload=True)
            
    def reload_settings(self, settings):
        """Reload settings from the provided values.
        
        Args:
            settings (dict): Settings to load
        """
        if not settings:
            return
            
        # Update settings
        self.settings = settings.copy()
        
        # Update UI control values to match settings
        for key, control in self.controls.items():
            if key == "volume" and control["type"] == "slider":
                control["value"] = self.settings["volume"]
            elif key == "reverb_amount" and control["type"] == "slider":
                control["value"] = self.settings["reverb_amount"]
            elif key == "show_note_names" and control["type"] == "toggle":
                control["value"] = self.settings["show_note_names"]
            elif key == "show_octave_markers" and control["type"] == "toggle":
                control["value"] = self.settings["show_octave_markers"]
            elif key == "audio_mode_samples" and control["type"] == "toggle":
                control["value"] = (self.settings["audio_mode"] == "samples")
            elif key == "difficulty" and control["type"] == "dropdown":
                control["value"] = self.settings["difficulty"]
            elif key == "falling_speed" and control["type"] == "slider":
                control["value"] = self.settings["falling_speed"]
            elif key == "hit_window" and control["type"] == "slider":
                control["value"] = self.settings["hit_window"]
            elif key == "prep_time" and control["type"] == "slider":
                control["value"] = self.settings["prep_time"]
            elif key == "show_performance_stats" and control["type"] == "toggle":
                control["value"] = self.settings["show_performance_stats"]
            elif key == "learning_visualization" and control["type"] == "dropdown":
                control["value"] = self.settings["learning_visualization"]

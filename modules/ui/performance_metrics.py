"""
Performance Metrics UI for the Comprehensive Piano Application
Displays statistics and performance metrics for learning mode
"""
import pygame
from typing import Dict, List, Tuple, Optional, Any
from collections import deque
import time
import math

class PerformanceMetrics:
    """Handles the display of performance metrics for learning mode."""
    
    def __init__(self):
        """Initialize the performance metrics component."""
        # Performance tracking
        self.total_notes = 0
        self.hit_notes = 0
        self.missed_notes = 0
        self.current_streak = 0
        self.max_streak = 0
        self.score = 0
        
        # Timing metrics
        self.timing_errors = deque(maxlen=50)  # Store last 50 timing errors (ms)
        self.accuracy_percentage = 100.0
        self.average_timing_error = 0.0
        
        # Grading levels for timing
        self.grade_thresholds = {
            "Perfect": 30,    # Within 30ms
            "Great": 70,      # Within 70ms
            "Good": 120,      # Within 120ms
            "OK": 200,        # Within 200ms
            "Miss": float('inf')  # Beyond threshold
        }
        
        # Last grade statistics for display
        self.grade_counts = {grade: 0 for grade in self.grade_thresholds}
        self.last_grade = None
        self.last_grade_time = 0
        self.last_note_time = 0
        
        # UI elements
        self.display_rect = None
        self.screen = None
        self.font = None
        self.title_font = None
        self.grade_font = None
        self.visible = True
        
        # History graph data
        self.timing_history_points = []
        self.graph_width = 300
        self.graph_height = 80
    
    def initialize(self, screen, font=None, title_font=None, grade_font=None):
        """Initialize the metrics display with pygame screen and fonts.
        
        Args:
            screen: Pygame screen surface
            font: Main font for UI text
            title_font: Font for titles
            grade_font: Font for grade display
        """
        self.screen = screen
        self.font = font or pygame.font.SysFont("Arial", 18)
        self.title_font = title_font or pygame.font.SysFont("Arial", 24, bold=True)
        self.grade_font = grade_font or pygame.font.SysFont("Arial", 36, bold=True)
        
        # Position the metrics display in the top right
        screen_width, screen_height = screen.get_size()
        self.display_rect = pygame.Rect(
            screen_width - 320,
            20,
            300,
            300
        )
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        self.total_notes = 0
        self.hit_notes = 0
        self.missed_notes = 0
        self.current_streak = 0
        self.max_streak = 0
        self.score = 0
        self.timing_errors.clear()
        self.accuracy_percentage = 100.0
        self.average_timing_error = 0.0
        self.grade_counts = {grade: 0 for grade in self.grade_thresholds}
        self.last_grade = None
        self.timing_history_points = []
    
    def note_hit(self, timing_error_ms: float):
        """Record a successfully hit note.
        
        Args:
            timing_error_ms (float): Timing error in milliseconds (absolute value)
        """
        self.total_notes += 1
        self.hit_notes += 1
        self.current_streak += 1
        self.max_streak = max(self.max_streak, self.current_streak)
        
        # Record timing error
        self.timing_errors.append(timing_error_ms)
        
        # Calculate average timing error
        if self.timing_errors:
            self.average_timing_error = sum(self.timing_errors) / len(self.timing_errors)
        
        # Calculate accuracy
        self.accuracy_percentage = (self.hit_notes / self.total_notes) * 100 if self.total_notes > 0 else 100.0
        
        # Determine grade based on timing
        self._calculate_grade(timing_error_ms)
        
        # Update score - better timing = higher score
        timing_multiplier = self._get_timing_multiplier(timing_error_ms)
        streak_multiplier = min(3.0, 1.0 + (self.current_streak / 50.0))  # Max 3x multiplier at 100 streak
        self.score += int(100 * timing_multiplier * streak_multiplier)
        
        # Update history graph
        self._update_timing_history(timing_error_ms)
        
        # Record time for animation
        self.last_note_time = time.time()
    
    def note_missed(self):
        """Record a missed note."""
        self.total_notes += 1
        self.missed_notes += 1
        self.current_streak = 0
        
        # Calculate accuracy
        self.accuracy_percentage = (self.hit_notes / self.total_notes) * 100 if self.total_notes > 0 else 0.0
        
        # Update grade counts
        self.grade_counts["Miss"] += 1
        self.last_grade = "Miss"
        self.last_grade_time = time.time()
        
        # Record time for animation
        self.last_note_time = time.time()
    
    def _calculate_grade(self, timing_error_ms: float):
        """Calculate grade based on timing error.
        
        Args:
            timing_error_ms (float): Timing error in milliseconds
        """
        for grade, threshold in sorted(self.grade_thresholds.items(), key=lambda x: x[1]):
            if timing_error_ms <= threshold:
                self.last_grade = grade
                self.grade_counts[grade] += 1
                self.last_grade_time = time.time()
                break
    
    def _get_timing_multiplier(self, timing_error_ms: float) -> float:
        """Get score multiplier based on timing accuracy.
        
        Args:
            timing_error_ms (float): Timing error in milliseconds
            
        Returns:
            float: Score multiplier (0.1 to 1.5)
        """
        # Perfect: 1.5x, Great: 1.2x, Good: 1.0x, OK: 0.5x, Miss: 0.1x
        if timing_error_ms <= self.grade_thresholds["Perfect"]:
            return 1.5
        elif timing_error_ms <= self.grade_thresholds["Great"]:
            return 1.2
        elif timing_error_ms <= self.grade_thresholds["Good"]:
            return 1.0
        elif timing_error_ms <= self.grade_thresholds["OK"]:
            return 0.5
        else:
            return 0.1
    
    def _update_timing_history(self, timing_error_ms: float):
        """Update the timing history graph data.
        
        Args:
            timing_error_ms (float): Timing error in milliseconds
        """
        # Limit the number of points in the graph
        if len(self.timing_history_points) >= self.graph_width // 3:
            self.timing_history_points.pop(0)
        
        # Add the new point
        self.timing_history_points.append(timing_error_ms)
    
    def draw(self):
        """Draw the performance metrics display."""
        if not self.visible or not self.screen:
            return
        
        # Draw panel background with transparency
        s = pygame.Surface(self.display_rect.size, pygame.SRCALPHA)
        s.fill((240, 240, 240, 220))  # Semi-transparent background
        self.screen.blit(s, self.display_rect.topleft)
        
        # Draw border
        pygame.draw.rect(self.screen, (180, 180, 180), self.display_rect, 2)
        
        # Draw title
        title_text = self.title_font.render("Performance", True, (0, 0, 0))
        self.screen.blit(
            title_text,
            (self.display_rect.x + 10, self.display_rect.y + 10)
        )
        
        # Current y position for drawing metrics
        y = self.display_rect.y + 50
        
        # Draw accuracy
        accuracy_text = self.font.render(
            f"Accuracy: {self.accuracy_percentage:.1f}%",
            True,
            (0, 0, 0)
        )
        self.screen.blit(accuracy_text, (self.display_rect.x + 10, y))
        y += 25
        
        # Draw streak
        streak_text = self.font.render(
            f"Streak: {self.current_streak} (Max: {self.max_streak})",
            True,
            (0, 0, 0)
        )
        self.screen.blit(streak_text, (self.display_rect.x + 10, y))
        y += 25
        
        # Draw score
        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            (0, 0, 0)
        )
        self.screen.blit(score_text, (self.display_rect.x + 10, y))
        y += 25
        
        # Draw timing
        if self.timing_errors:
            timing_text = self.font.render(
                f"Avg. Timing: {self.average_timing_error:.1f}ms",
                True,
                (0, 0, 0)
            )
            self.screen.blit(timing_text, (self.display_rect.x + 10, y))
        y += 35
        
        # Draw timing history graph
        self._draw_timing_graph(y)
        y += self.graph_height + 20
        
        # Draw grade distribution
        self._draw_grade_distribution(y)
        
        # Draw last grade animation if recent
        self._draw_last_grade_animation()
    
    def _draw_timing_graph(self, y):
        """Draw the timing error history graph.
        
        Args:
            y (int): Y-coordinate to start drawing
        """
        if not self.timing_history_points:
            return
            
        # Draw graph borders
        graph_rect = pygame.Rect(
            self.display_rect.x + 10,
            y,
            self.graph_width,
            self.graph_height
        )
        pygame.draw.rect(self.screen, (200, 200, 200), graph_rect, 1)
        
        # Draw graph title
        graph_title = self.font.render("Timing History", True, (0, 0, 0))
        self.screen.blit(
            graph_title,
            (
                graph_rect.x + (graph_rect.width - graph_title.get_width()) // 2,
                graph_rect.y - 20
            )
        )
        
        # Draw horizontal lines for thresholds
        for grade, threshold in self.grade_thresholds.items():
            if grade != "Miss":  # Don't draw line for "Miss"
                line_y = graph_rect.y + min(
                    graph_rect.height - 2,
                    int((threshold / 200) * graph_rect.height)
                )
                
                # Draw threshold line
                pygame.draw.line(
                    self.screen,
                    (200, 200, 200),
                    (graph_rect.x + 1, line_y),
                    (graph_rect.x + graph_rect.width - 1, line_y),
                    1
                )
                
                # Draw threshold label
                label = self.font.render(grade, True, (150, 150, 150))
                self.screen.blit(
                    label,
                    (graph_rect.x + graph_rect.width - label.get_width() - 2, line_y - 15)
                )
        
        # Draw timing points
        if len(self.timing_history_points) > 1:
            points = []
            for i, error in enumerate(self.timing_history_points):
                x = graph_rect.x + 5 + i * 3
                # Scale error to graph height (max displayable error is 200ms)
                y_pos = graph_rect.y + min(
                    graph_rect.height - 2,
                    int((min(error, 200) / 200) * graph_rect.height)
                )
                points.append((x, y_pos))
            
            # Draw connecting lines
            if len(points) > 1:
                pygame.draw.lines(self.screen, (100, 100, 200), False, points, 2)
    
    def _draw_grade_distribution(self, y):
        """Draw the grade distribution chart.
        
        Args:
            y (int): Y-coordinate to start drawing
        """
        # Calculate total graded notes
        total_graded = sum(self.grade_counts.values())
        if total_graded == 0:
            return
        
        # Draw title
        dist_title = self.font.render("Grade Distribution", True, (0, 0, 0))
        self.screen.blit(dist_title, (self.display_rect.x + 10, y))
        
        # Colors for each grade
        grade_colors = {
            "Perfect": (100, 200, 255),
            "Great": (100, 255, 100),
            "Good": (255, 255, 100),
            "OK": (255, 180, 100),
            "Miss": (255, 100, 100)
        }
        
        # Draw bar chart
        bar_height = 15
        max_bar_width = self.display_rect.width - 100
        
        for i, (grade, count) in enumerate(
            sorted(self.grade_counts.items(), 
                  key=lambda x: list(self.grade_thresholds.keys()).index(x[0]))
        ):
            # Skip grades with no hits
            if count == 0:
                continue
                
            # Calculate percentage
            percentage = (count / total_graded) * 100
            
            # Draw label
            grade_y = y + 25 + (i * (bar_height + 10))
            label = self.font.render(f"{grade}: ", True, (0, 0, 0))
            self.screen.blit(label, (self.display_rect.x + 10, grade_y))
            
            # Draw bar
            bar_width = int((percentage / 100) * max_bar_width)
            bar_rect = pygame.Rect(
                self.display_rect.x + 80,
                grade_y + 2,
                bar_width,
                bar_height
            )
            pygame.draw.rect(self.screen, grade_colors.get(grade, (200, 200, 200)), bar_rect)
            
            # Draw percentage
            pct_text = self.font.render(f"{percentage:.1f}%", True, (0, 0, 0))
            self.screen.blit(
                pct_text,
                (bar_rect.x + bar_width + 5, bar_rect.y)
            )
    
    def _draw_last_grade_animation(self):
        """Draw the last grade animation if it's recent."""
        if not self.last_grade:
            return
            
        # Only show animation for 1.5 seconds
        time_since_grade = time.time() - self.last_grade_time
        if time_since_grade > 1.5:
            return
        
        # Grade colors
        grade_colors = {
            "Perfect": (100, 200, 255),
            "Great": (100, 255, 100),
            "Good": (255, 255, 100),
            "OK": (255, 180, 100),
            "Miss": (255, 100, 100)
        }
        
        # Calculate animation properties
        alpha = max(0, 255 - int(time_since_grade * 170))
        scale = min(1.3, 1 + time_since_grade * 0.5)
        
        # Render grade text
        color = grade_colors.get(self.last_grade, (200, 200, 200))
        grade_surf = self.grade_font.render(self.last_grade, True, color)
        
        # Scale text
        scaled_width = int(grade_surf.get_width() * scale)
        scaled_height = int(grade_surf.get_height() * scale)
        scaled_surf = pygame.transform.scale(grade_surf, (scaled_width, scaled_height))
        
        # Add transparency
        scaled_surf.set_alpha(alpha)
        
        # Center on screen
        screen_width, screen_height = self.screen.get_size()
        x = (screen_width - scaled_width) // 2
        y = (screen_height - scaled_height) // 2
        
        # Draw animation
        self.screen.blit(scaled_surf, (x, y))
    
    def get_score(self):
        """Get the current score.
        
        Returns:
            int: Current score
        """
        return self.score
    
    def get_accuracy(self):
        """Get the current accuracy percentage.
        
        Returns:
            float: Accuracy percentage
        """
        return self.accuracy_percentage
    
    def get_grade_counts(self):
        """Get the grade distribution counts.
        
        Returns:
            Dict[str, int]: Counts for each grade
        """
        return self.grade_counts.copy()
    
    def show(self):
        """Show the performance metrics display."""
        self.visible = True
    
    def hide(self):
        """Hide the performance metrics display."""
        self.visible = False
    
    def toggle_visibility(self):
        """Toggle the visibility of the performance metrics display."""
        self.visible = not self.visible
    
    def resize(self, screen_width, screen_height):
        """Handle window resize events.
        
        Args:
            screen_width (int): New screen width
            screen_height (int): New screen height
        """
        # Reposition the metrics display in the top right
        self.display_rect = pygame.Rect(
            screen_width - 320,
            20,
            300,
            300
        )

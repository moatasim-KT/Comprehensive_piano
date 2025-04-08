# Comprehensive Piano Application

An integrated piano visualization, learning, and playing application combining multiple piano-related functionalities in a cohesive, modular structure.

## Features

- **Piano Visualization**: Interactive piano keyboard with customizable display options
- **MIDI File Parsing and Playback**: Load and play MIDI files with visual feedback
- **Dual Audio Engine**: Support for both sample-based and synthesized piano sounds
- **Learning Mode**: Visual note guidance with falling notes and performance metrics
- **Performance Analytics**: Track accuracy, timing, and improvement over time
- **Multiple Input Methods**: Support for computer keyboard and MIDI devices
- **Music Theory Tools**: Generate scales, chords, and progressions

## Project Structure

```
Comprehensive_piano/
├── main.py                 # Main entry point
├── modules/                # Core functionality modules
│   ├── audio_engine.py     # Audio playback and sound generation
│   ├── input_handler.py    # Keyboard and MIDI input processing
│   ├── midi_parser.py      # MIDI file parsing and analysis
│   ├── music_theory.py     # Music theory utilities
│   ├── ui/                 # UI components
│   │   ├── falling_notes.py      # Falling notes visualization
│   │   ├── performance_metrics.py # Learning statistics display
│   │   ├── piano_display.py       # Piano keyboard visualization
│   │   ├── settings.py            # Settings interface
│   │   └── ui_manager.py          # UI coordination
│   └── visualizer.py       # Piano visualization
└── utils/                  # Helper utilities
    └── helpers.py          # Common helper functions
```

## Requirements

- Python 3.7+
- pygame
- mido (for MIDI file parsing)
- numpy
- python-rtmidi (for MIDI device support)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/comprehensive-piano.git
   cd comprehensive-piano
   ```

2. Install dependencies:
   ```
   pip install pygame mido numpy python-rtmidi
   ```

## Usage

### Basic Usage

Run the application with:
```
python main.py
```

### Command Line Options

```
python main.py [options]

Options:
  --midi, -m FILE       Path to MIDI file to load on startup
  --fullscreen, -f      Start in fullscreen mode
  --learning, -l        Start in learning mode
```

### Controls

#### Application Controls
- **F3**: Toggle FPS display
- **ESC**: Close settings menu

#### Piano Keyboard
- Computer keyboard: Play notes using the keyboard (mapping shown in the application)
- MIDI keyboard: Connect a MIDI device for full piano control

#### Modes
- **Free Play**: Practice with visual feedback
- **Learning Mode**: Follow along with MIDI files to improve skills
- **Settings**: Customize the application behavior and appearance

## Learning Mode

The learning mode guides you through playing a MIDI file with:
- Visual guidance via falling notes
- Real-time performance metrics (accuracy, timing, score)
- Graded feedback on note accuracy

## Customization

Access the settings menu to customize:
- Audio settings (volume, reverb, sample/synthesis mode)
- Display options (note names, octave markers)
- Learning mode parameters (note speed, difficulty)
- Performance metrics visibility

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

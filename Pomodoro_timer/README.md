# Pomodoro Timer

A desktop Pomodoro timer built with Python and tkinter. It follows the standard Pomodoro technique — focused work sessions separated by short breaks, with a longer break after every four sessions. The app includes a circular countdown display, automatic session progression, and synthesised lo-fi background music that plays without any external audio files.

## Requirements

- Python 3.10+
- tkinter (usually bundled with Python; on Debian/Ubuntu: `sudo apt install python3-tk`)
- numpy and pygame (for music synthesis and playback)

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## How it works

When you press **Start**, the timer counts down from 25 minutes. When it reaches zero, the app rings a bell, automatically switches to the next session, and waits for you to press Start again. After four completed focus sessions, the short break is replaced by a 15-minute long break, then the cycle repeats.

The three buttons work as follows:

- **Start / Pause** — begins the countdown or pauses it mid-session
- **Reset** — stops the timer and restores the current session's full duration without changing the mode
- **Skip** — ends the current session immediately and advances to the next one, the same as if the timer had run out naturally

The four dots below the timer represent your progress through the current four-pomodoro cycle. Each dot fills in as you complete a focus session and clears again after the long break.

The colour theme changes automatically with each mode — red during focus sessions, green during short breaks, and blue during long breaks — so you can tell at a glance where you are in the cycle.

## Music

Background music starts when you press Start and stops when you pause or reset. The audio is generated entirely in Python using numpy, so no audio files are needed. Two loops are synthesised when the app launches (taking a second or two in the background) and then looped seamlessly:

- **Focus sessions** — a deep, warm drone built on a C2 bass with soft harmonics, paired with a slow pentatonic arpeggio in the lower registers. The tone has a lo-fi, slightly tape-worn quality from added vinyl noise and heavy reverb.
- **Breaks** — a dreamier Fmaj7 chord pad with very sparse, widely spaced melody notes and a long reverb tail, giving more breathing room between sounds.

Use the **♪ Music on / Muted** button to toggle the music on or off, and the slider next to it to adjust the volume independently of your system volume.

## Configuration

Edit the constants at the top of `main.py` to change session durations or the long-break interval:

```python
WORK_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
POMODOROS_BEFORE_LONG_BREAK = 4
```

Colors per mode are in the `COLORS` dict in the same file. The music synthesis parameters (note patterns, reverb, drone frequencies) are in `audio.py`.

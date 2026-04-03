"""
Synthesised lo-fi ambient loops for the Pomodoro timer.
Requires: numpy, pygame
"""
import threading
import numpy as np
import pygame

SAMPLE_RATE = 44100
LOOP_SECONDS = 16  # must produce whole sine cycles for each freq


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _q(freq: float) -> float:
    """Snap a frequency so it completes an exact whole number of cycles
    over LOOP_SECONDS — gives a perfectly seamless loop."""
    return round(freq * LOOP_SECONDS) / LOOP_SECONDS


def _sine(freq: float, n: int, amp: float) -> np.ndarray:
    t = np.linspace(0, LOOP_SECONDS, n, endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)


def _warm_sine(freq: float, n: int, amp: float) -> np.ndarray:
    """Warmer pad tone: fundamental + soft 3rd & 5th harmonics (triangle-ish)."""
    t = np.linspace(0, LOOP_SECONDS, n, endpoint=False)
    wave  = amp        * np.sin(2 * np.pi * freq * t)
    wave += (amp / 9)  * np.sin(2 * np.pi * freq * 3 * t)
    wave += (amp / 25) * np.sin(2 * np.pi * freq * 5 * t)
    return wave


def _note(freq: float, dur: float, amp: float, vibrato_hz: float = 4.0) -> np.ndarray:
    """Single note: gentle vibrato, warm harmonic, slow fade-in/out."""
    n = int(dur * SAMPLE_RATE)
    t = np.linspace(0, dur, n, endpoint=False)
    lfo = 1.0 + 0.003 * np.sin(2 * np.pi * vibrato_hz * t)
    phase = np.cumsum(2 * np.pi * freq * lfo / SAMPLE_RATE)
    wave = amp * np.sin(phase)
    wave += (amp * 0.12) * np.sin(3 * phase)   # soft 3rd harmonic
    attack  = min(int(0.15 * SAMPLE_RATE), n // 3)
    release = min(int(0.28 * SAMPLE_RATE), n // 3)
    wave[:attack]  *= np.linspace(0, 1, attack)
    wave[-release:] *= np.linspace(1, 0, release)
    return wave


def _place(buf: np.ndarray, wave: np.ndarray, t_start: float) -> None:
    start = int(t_start * SAMPLE_RATE)
    end = start + len(wave)
    if end <= len(buf):
        buf[start:end] += wave


def _reverb(sig: np.ndarray, delay_s: float = 0.12, decay: float = 0.28,
            taps: int = 3) -> np.ndarray:
    out = sig.copy()
    d = int(delay_s * SAMPLE_RATE)
    for k in range(1, taps + 1):
        echo = np.zeros_like(sig)
        shift = d * k
        echo[shift:] = sig[:-shift] * (decay ** k)
        out += echo
    return out


def _to_sound(mono: np.ndarray) -> pygame.mixer.Sound:
    peak = np.max(np.abs(mono))
    if peak > 0:
        mono = mono / peak * 0.78
    s16 = (mono * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack([s16, s16]))
    return pygame.sndarray.make_sound(stereo)


# ---------------------------------------------------------------------------
# Loop generation
# ---------------------------------------------------------------------------

def _build_work_loop() -> pygame.mixer.Sound:
    """Deep, warm lo-fi loop — C major pentatonic, chilled pace."""
    n = int(SAMPLE_RATE * LOOP_SECONDS)
    mix = np.zeros(n)

    # --- Deep warm pad: C2 · G2 · C3 ---
    for f, a in [(_q(65.41), 0.14), (_q(98.00), 0.10), (_q(130.81), 0.08)]:
        mix += _warm_sine(f, n, a)

    # Very slow breathing tremolo
    t = np.linspace(0, LOOP_SECONDS, n, endpoint=False)
    mix *= 1.0 + 0.06 * np.sin(2 * np.pi * 0.06 * t)

    # --- Sparse melody: 5 notes, ~3 s apart, lower register ---
    # C3=130.81  E3=164.81  G3=196.00  A3=220.00  C4=261.63
    melody = [
        (_q(130.81), 0.0,  2.8, 0.14),
        (_q(196.00), 3.2,  2.8, 0.12),
        (_q(164.81), 6.5,  2.8, 0.12),
        (_q(220.00), 9.8,  3.0, 0.11),
        (_q(196.00), 13.0, 2.6, 0.12),
    ]
    for freq, t_s, dur, amp in melody:
        _place(mix, _note(freq, dur, amp, vibrato_hz=4.0), t_s)

    # --- Heavy vinyl texture: more noise, wider low-pass kernel ---
    noise = np.random.default_rng(42).standard_normal(n) * 0.016
    mix += np.convolve(noise, np.ones(150) / 150, mode="same")

    mix = _reverb(mix, delay_s=0.18, decay=0.38, taps=4)
    return _to_sound(mix)


def _build_break_loop() -> pygame.mixer.Sound:
    """Dreamy Fmaj7 loop — very sparse, lots of reverb tail."""
    n = int(SAMPLE_RATE * LOOP_SECONDS)
    mix = np.zeros(n)

    # Fmaj7 pad: F2 · C3 · F3 · A3 · E4
    for f, a in [(_q(87.31), 0.13), (_q(130.81), 0.10),
                 (_q(174.61), 0.09), (_q(220.00), 0.08), (_q(329.63), 0.06)]:
        mix += _warm_sine(f, n, a)

    t = np.linspace(0, LOOP_SECONDS, n, endpoint=False)
    mix *= 1.0 + 0.04 * np.sin(2 * np.pi * 0.05 * t)

    # Very sparse melody: 3 notes with long gaps
    # F4=349.23  C4=261.63  A3=220.00
    melody = [
        (_q(349.23), 0.5,  3.5, 0.10),
        (_q(261.63), 6.0,  3.5, 0.10),
        (_q(349.23), 12.0, 3.5, 0.10),
    ]
    for freq, t_s, dur, amp in melody:
        _place(mix, _note(freq, dur, amp, vibrato_hz=3.5), t_s)

    noise = np.random.default_rng(7).standard_normal(n) * 0.013
    mix += np.convolve(noise, np.ones(180) / 180, mode="same")

    mix = _reverb(mix, delay_s=0.22, decay=0.42, taps=4)
    return _to_sound(mix)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class AudioPlayer:
    """Thread-safe lo-fi loop player."""

    def __init__(self) -> None:
        self._ready = False
        self._muted = False
        self._volume = 0.45
        self._loops: dict[str, pygame.mixer.Sound] = {}
        self._active: pygame.mixer.Sound | None = None
        self._lock = threading.Lock()
        self.on_ready: "Callable[[], None] | None" = None  # set by UI

    def init_async(self) -> None:
        """Build loops in a background thread; calls self.on_ready when done."""
        threading.Thread(target=self._build, daemon=True).start()

    def _build(self) -> None:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, 512)
        pygame.mixer.init()
        self._loops["work"] = _build_work_loop()
        self._loops["break"] = _build_break_loop()
        for s in self._loops.values():
            s.set_volume(self._volume)
        self._ready = True
        if self.on_ready:
            self.on_ready()

    # --- playback ---

    def play(self, mode: str) -> None:
        if not self._ready or self._muted:
            return
        key = "work" if mode == "work" else "break"
        with self._lock:
            sound = self._loops.get(key)
            if sound is self._active:
                return  # already playing
            if self._active:
                self._active.stop()
            self._active = sound
            if sound:
                sound.play(loops=-1)

    def stop(self) -> None:
        with self._lock:
            if self._active:
                self._active.stop()
                self._active = None

    def toggle_mute(self) -> bool:
        """Returns True if now muted."""
        self._muted = not self._muted
        if self._muted:
            self.stop()
        return self._muted

    def set_volume(self, v: float) -> None:
        self._volume = max(0.0, min(1.0, v))
        for s in self._loops.values():
            s.set_volume(self._volume)

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def muted(self) -> bool:
        return self._muted

import tkinter as tk
from tkinter import font

try:
    import audio as _audio
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False

# --- Configuration ---
WORK_MINUTES = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES = 15
POMODOROS_BEFORE_LONG_BREAK = 4

COLORS = {
    "work":        {"bg": "#c0392b", "fg": "#ffffff", "btn": "#922b21"},
    "short_break": {"bg": "#27ae60", "fg": "#ffffff", "btn": "#1e8449"},
    "long_break":  {"bg": "#2980b9", "fg": "#ffffff", "btn": "#1f618d"},
}

MODES = {
    "work":        WORK_MINUTES * 60,
    "short_break": SHORT_BREAK_MINUTES * 60,
    "long_break":  LONG_BREAK_MINUTES * 60,
}

MODE_LABELS = {
    "work":        "Focus",
    "short_break": "Short Break",
    "long_break":  "Long Break",
}


class PomodoroApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Pomodoro Timer")
        self.root.resizable(False, False)

        self.mode = "work"
        self.time_left = MODES[self.mode]
        self.running = False
        self.pomodoros_done = 0
        self._after_id: str | None = None

        # Audio
        self._player: "_audio.AudioPlayer | None" = None
        if _AUDIO_AVAILABLE:
            self._player = _audio.AudioPlayer()
            self._player.on_ready = self._on_audio_ready

        self._build_ui()
        self._apply_theme()
        self._update_display()

        if self._player:
            self._player.init_async()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.root.configure(padx=40, pady=30)

        # Mode label
        self.mode_label = tk.Label(self.root, text="", font=("Helvetica", 14))
        self.mode_label.pack()

        # Canvas for circular progress ring
        self.canvas_size = 240
        self.ring_width = 12
        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_size,
            height=self.canvas_size,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(10, 0))

        self.timer_font = font.Font(family="Helvetica", size=48, weight="bold")
        cx = cy = self.canvas_size // 2
        self.canvas.create_oval(
            self.ring_width, self.ring_width,
            self.canvas_size - self.ring_width,
            self.canvas_size - self.ring_width,
            outline="", fill="", tags="bg_circle",
        )
        self.canvas.create_arc(
            self.ring_width, self.ring_width,
            self.canvas_size - self.ring_width,
            self.canvas_size - self.ring_width,
            start=90, extent=360,
            outline="", fill="", style=tk.ARC,
            width=self.ring_width, tags="arc",
        )
        self.canvas.create_text(
            cx, cy, text="", font=self.timer_font, tags="time_text",
        )

        # Pomodoro dots
        self.dots_frame = tk.Frame(self.root)
        self.dots_frame.pack(pady=(8, 0))
        self.dot_labels: list[tk.Label] = []
        for _ in range(POMODOROS_BEFORE_LONG_BREAK):
            dot = tk.Label(self.dots_frame, text="●", font=("Helvetica", 14))
            dot.pack(side=tk.LEFT, padx=3)
            self.dot_labels.append(dot)

        # Main buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=(20, 0))

        btn_cfg = dict(font=("Helvetica", 12, "bold"), bd=0, relief=tk.FLAT,
                       padx=18, pady=8, cursor="hand2")

        self.start_btn = tk.Button(btn_frame, text="Start", command=self._toggle, **btn_cfg)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.reset_btn = tk.Button(btn_frame, text="Reset", command=self._reset, **btn_cfg)
        self.reset_btn.grid(row=0, column=1, padx=6)

        self.skip_btn = tk.Button(btn_frame, text="Skip", command=self._skip, **btn_cfg)
        self.skip_btn.grid(row=0, column=2, padx=6)

        # Audio controls (only shown when audio is available)
        if _AUDIO_AVAILABLE:
            audio_frame = tk.Frame(self.root)
            audio_frame.pack(pady=(14, 0))

            small_btn = dict(font=("Helvetica", 11), bd=0, relief=tk.FLAT,
                             padx=10, pady=5, cursor="hand2")

            self.music_btn = tk.Button(
                audio_frame, text="♪  Loading…",
                command=self._toggle_mute, state=tk.DISABLED, **small_btn,
            )
            self.music_btn.grid(row=0, column=0, padx=(0, 10))

            self._vol_var = tk.DoubleVar(value=0.45)
            self.vol_slider = tk.Scale(
                audio_frame, from_=0.0, to=1.0, resolution=0.01,
                orient=tk.HORIZONTAL, length=110, showvalue=False,
                variable=self._vol_var, command=self._on_volume,
                bd=0, highlightthickness=0, sliderrelief=tk.FLAT,
            )
            self.vol_slider.grid(row=0, column=1)
        else:
            self.music_btn = None
            self.vol_slider = None

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        c = COLORS[self.mode]
        bg, fg, btn_bg = c["bg"], c["fg"], c["btn"]

        self.root.configure(bg=bg)
        self.mode_label.configure(bg=bg, fg=fg)
        self.dots_frame.configure(bg=bg)
        self.canvas.configure(bg=bg)

        self.canvas.itemconfig("bg_circle", outline=btn_bg, width=self.ring_width)
        self.canvas.coords(
            "bg_circle",
            self.ring_width, self.ring_width,
            self.canvas_size - self.ring_width,
            self.canvas_size - self.ring_width,
        )
        self.canvas.itemconfig("arc", outline=fg)
        self.canvas.itemconfig("time_text", fill=fg)

        for btn in (self.start_btn, self.reset_btn, self.skip_btn):
            btn.configure(bg=btn_bg, fg=fg, activebackground=bg, activeforeground=fg)

        if self.music_btn:
            self.music_btn.configure(bg=btn_bg, fg=fg,
                                     activebackground=bg, activeforeground=fg)
        if self.vol_slider:
            self.vol_slider.configure(bg=bg, fg=fg, troughcolor=btn_bg,
                                      activebackground=fg)

        # Frame containing audio controls shares bg
        if _AUDIO_AVAILABLE and self.music_btn:
            self.music_btn.master.configure(bg=bg)

        for i, dot in enumerate(self.dot_labels):
            filled = i < (self.pomodoros_done % POMODOROS_BEFORE_LONG_BREAK)
            dot.configure(bg=bg, fg=fg if filled else btn_bg)

    # ------------------------------------------------------------------
    # Display update
    # ------------------------------------------------------------------

    def _update_display(self) -> None:
        minutes, seconds = divmod(self.time_left, 60)
        time_str = f"{minutes:02d}:{seconds:02d}"
        self.canvas.itemconfig("time_text", text=time_str)
        self.root.title(f"{time_str} — {MODE_LABELS[self.mode]}")

        total = MODES[self.mode]
        self.canvas.itemconfig("arc", extent=(self.time_left / total) * 360)

        self.mode_label.configure(text=MODE_LABELS[self.mode])
        self.start_btn.configure(text="Pause" if self.running else "Start")

        c = COLORS[self.mode]
        for i, dot in enumerate(self.dot_labels):
            filled = i < (self.pomodoros_done % POMODOROS_BEFORE_LONG_BREAK)
            dot.configure(fg=c["fg"] if filled else c["btn"])

    # ------------------------------------------------------------------
    # Audio callbacks
    # ------------------------------------------------------------------

    def _on_audio_ready(self) -> None:
        """Called from background thread when loops are synthesised."""
        self.root.after(0, self._audio_ready_ui)

    def _audio_ready_ui(self) -> None:
        if self.music_btn:
            self.music_btn.configure(text="♪  Music on", state=tk.NORMAL)

    def _toggle_mute(self) -> None:
        if not self._player:
            return
        muted = self._player.toggle_mute()
        if muted:
            self.music_btn.configure(text="♪  Muted")
        else:
            self.music_btn.configure(text="♪  Music on")
            if self.running:
                self._player.play(self.mode)

    def _on_volume(self, _: str) -> None:
        if self._player:
            self._player.set_volume(self._vol_var.get())

    # ------------------------------------------------------------------
    # Timer logic
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        if not self.running:
            return
        if self.time_left > 0:
            self.time_left -= 1
            self._update_display()
            self._after_id = self.root.after(1000, self._tick)
        else:
            self._session_complete()

    def _session_complete(self) -> None:
        self.running = False
        if self._player:
            self._player.stop()
        self.root.bell()
        if self.mode == "work":
            self.pomodoros_done += 1
            next_mode = (
                "long_break"
                if self.pomodoros_done % POMODOROS_BEFORE_LONG_BREAK == 0
                else "short_break"
            )
        else:
            next_mode = "work"
        self._set_mode(next_mode)

    def _toggle(self) -> None:
        if self.running:
            self.running = False
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            if self._player:
                self._player.stop()
        else:
            self.running = True
            if self._player:
                self._player.play(self.mode)
            self._tick()
        self._update_display()

    def _reset(self) -> None:
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        if self._player:
            self._player.stop()
        self.time_left = MODES[self.mode]
        self._update_display()

    def _skip(self) -> None:
        self.running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self._session_complete()

    def _set_mode(self, mode: str) -> None:
        self.mode = mode
        self.time_left = MODES[mode]
        self._apply_theme()
        self._update_display()


# ------------------------------------------------------------------

def main() -> None:
    root = tk.Tk()
    PomodoroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

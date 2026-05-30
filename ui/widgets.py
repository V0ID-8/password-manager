"""Reusable UI widgets: StrengthMeter, Toast notification."""
import customtkinter as ctk

# Color palette for strength levels
STRENGTH_COLORS = {
    0: "#e74c3c",  # red
    1: "#e67e22",  # orange
    2: "#f1c40f",  # yellow
    3: "#2ecc71",  # green
    4: "#27ae60",  # dark green
}


class StrengthMeter(ctk.CTkFrame):
    """Horizontal bar + label showing password strength."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._bar_bg = ctk.CTkFrame(self, height=6, corner_radius=3, fg_color="#3a3a3a")
        self._bar_bg.pack(fill="x", pady=(4, 2))
        self._bar_bg.pack_propagate(False)

        self._bar_fill = ctk.CTkFrame(self._bar_bg, height=6, corner_radius=3, fg_color="#3a3a3a")
        self._bar_fill.place(relx=0, rely=0, relwidth=0, relheight=1)

        self._label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="#888888")
        self._label.pack(anchor="w")

    def update_strength(self, score: int, label: str):
        color = STRENGTH_COLORS.get(score, "#3a3a3a")
        fraction = (score + 1) / 5 if label != "None" else 0
        self._bar_fill.place_configure(relwidth=fraction)
        self._bar_fill.configure(fg_color=color if fraction > 0 else "#3a3a3a")
        self._label.configure(text=label if label != "None" else "", text_color=color)

    def clear(self):
        self._bar_fill.place_configure(relwidth=0)
        self._label.configure(text="")


class Toast(ctk.CTkLabel):
    """Temporary notification label that fades after a delay."""

    SUCCESS_COLOR = "#2ecc71"
    ERROR_COLOR = "#e74c3c"
    INFO_COLOR = "#3498db"

    def __init__(self, master, **kwargs):
        super().__init__(master, text="", font=ctk.CTkFont(size=12),
                         fg_color="transparent", **kwargs)
        self._job = None

    def show(self, message: str, kind: str = "success", duration_ms: int = 3000):
        if self._job:
            self.after_cancel(self._job)
        color = {"success": self.SUCCESS_COLOR,
                 "error": self.ERROR_COLOR,
                 "info": self.INFO_COLOR}.get(kind, self.INFO_COLOR)
        self.configure(text=message, text_color=color)
        self._job = self.after(duration_ms, self._clear)

    def _clear(self):
        self.configure(text="")
        self._job = None

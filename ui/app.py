"""Root application window and main frame with sidebar navigation."""
import customtkinter as ctk
from vault import Vault
from ui.unlock import UnlockFrame

# Forward declarations resolved at import time via string-based lazy imports
# to avoid circular dependencies with entry_list / entry_detail / generator_view.


class App(ctk.CTk):
    def __init__(self, vault: Vault):
        super().__init__()
        self._vault = vault
        self._inactivity_job = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("CrypticRocket")
        self.geometry("1100x650")
        self.minsize(800, 500)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._current_frame: ctk.CTkFrame | None = None
        self._show_unlock()

    # ------------------------------------------------------------------
    # Screen switching
    # ------------------------------------------------------------------

    def _show_unlock(self):
        self._cancel_inactivity()
        if self._current_frame:
            self._current_frame.destroy()
        frame = UnlockFrame(self, self._vault, on_unlock=self._show_main)
        frame.grid(row=0, column=0, sticky="nsew")
        self._current_frame = frame

    def _show_main(self):
        if self._current_frame:
            self._current_frame.destroy()
        frame = MainFrame(self, self._vault, on_lock=self._lock)
        frame.grid(row=0, column=0, sticky="nsew")
        self._current_frame = frame
        self._reset_inactivity()
        self._bind_activity()

    def _lock(self):
        self._vault.lock()
        self._show_unlock()

    # ------------------------------------------------------------------
    # Inactivity auto-lock (5 minutes)
    # ------------------------------------------------------------------

    def _bind_activity(self):
        for event in ("<Motion>", "<KeyPress>", "<ButtonPress>"):
            self.bind_all(event, self._reset_inactivity, add="+")

    def _reset_inactivity(self, _event=None):
        self._cancel_inactivity()
        self._inactivity_job = self.after(300_000, self._lock)

    def _cancel_inactivity(self):
        if self._inactivity_job:
            self.after_cancel(self._inactivity_job)
            self._inactivity_job = None


# Sidebar button spec: (label, nav_key)
_NAV_ITEMS = [
    ("  All Entries", "entries"),
    ("  Add Entry", "add"),
    ("  Generator", "generate"),
]


class MainFrame(ctk.CTkFrame):
    def __init__(self, master: App, vault: Vault, on_lock, **kwargs):
        super().__init__(master, fg_color="#181825", **kwargs)
        self._vault = vault
        self._on_lock = on_lock

        # Lazy imports here to avoid circular deps at module level
        from ui.entry_list import EntryListView
        from ui.generator_view import GeneratorView

        self._view_classes = {
            "entries": EntryListView,
            "generate": GeneratorView,
        }
        self._active_view: ctk.CTkFrame | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ---- Sidebar ----
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1e1e2e")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            sidebar, text="🔐 CrypticRocket",
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#cdd6f4"
        ).grid(row=0, column=0, padx=16, pady=(24, 20), sticky="w")

        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for i, (label, key) in enumerate(_NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                height=38, corner_radius=8,
                fg_color="transparent", hover_color="#313244",
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.show_view(k),
            )
            btn.grid(row=i + 1, column=0, padx=10, pady=3, sticky="ew")
            self._nav_btns[key] = btn

        ctk.CTkButton(
            sidebar, text="  Export / Import", anchor="w",
            height=38, corner_radius=8,
            fg_color="transparent", hover_color="#313244",
            font=ctk.CTkFont(size=13), text_color="#a6adc8",
            command=self._open_export_import,
        ).grid(row=10, column=0, padx=10, pady=3, sticky="ew")

        ctk.CTkButton(
            sidebar, text="  Lock vault", anchor="w",
            height=38, corner_radius=8,
            fg_color="transparent", hover_color="#313244",
            font=ctk.CTkFont(size=13), text_color="#f38ba8",
            command=on_lock,
        ).grid(row=11, column=0, padx=10, pady=(0, 16), sticky="ew")

        # ---- Content area ----
        self._content = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self.show_view("entries")

    def show_view(self, key: str):
        # Highlight active nav button
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color="#313244" if k == key else "transparent")

        if self._active_view:
            self._active_view.destroy()

        if key == "add":
            from ui.add_dialog import AddDialog
            AddDialog(self, self._vault, on_save=lambda: self.show_view("entries"))
            return

        cls = self._view_classes.get(key)
        if cls:
            view = cls(self._content, self._vault,
                       on_navigate=self.show_view)
            view.grid(row=0, column=0, sticky="nsew")
            self._active_view = view

    def _open_export_import(self):
        from ui.export_import import ExportImportDialog
        ExportImportDialog(self, self._vault, on_reimport=self._on_lock)

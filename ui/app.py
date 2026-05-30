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
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color="#13131f")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        # row 5 gets the stretch so bottom buttons stick to the bottom
        sidebar.grid_rowconfigure(5, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        # Branding
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=16, pady=(22, 6), sticky="ew")
        ctk.CTkLabel(brand, text="🔐", font=ctk.CTkFont(size=18)).pack(side="left")
        ctk.CTkLabel(brand, text=" CrypticRocket",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#cdd6f4").pack(side="left")

        # Thin separator under branding
        ctk.CTkFrame(sidebar, height=1, fg_color="#232336", corner_radius=0).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Main nav buttons
        self._nav_btns: dict[str, ctk.CTkButton] = {}
        for i, (label, key) in enumerate(_NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                height=40, corner_radius=8,
                fg_color="transparent", hover_color="#252540",
                text_color="#a6adc8",
                font=ctk.CTkFont(size=13),
                command=lambda k=key: self.show_view(k),
            )
            btn.grid(row=i + 2, column=0, padx=10, pady=2, sticky="ew")
            self._nav_btns[key] = btn

        # row 5 is the spacer (weight=1 above) — bottom buttons go in rows 6,7,8

        # Thin separator above bottom actions
        ctk.CTkFrame(sidebar, height=1, fg_color="#232336", corner_radius=0).grid(
            row=6, column=0, sticky="ew", padx=16, pady=(0, 6))

        ctk.CTkButton(
            sidebar, text="  Export / Import", anchor="w",
            height=38, corner_radius=8,
            fg_color="transparent", hover_color="#252540",
            font=ctk.CTkFont(size=12), text_color="#585b70",
            command=self._open_export_import,
        ).grid(row=7, column=0, padx=10, pady=2, sticky="ew")

        ctk.CTkButton(
            sidebar, text="  Lock vault", anchor="w",
            height=38, corner_radius=8,
            fg_color="transparent", hover_color="#252540",
            font=ctk.CTkFont(size=12), text_color="#f38ba8",
            command=on_lock,
        ).grid(row=8, column=0, padx=10, pady=(2, 16), sticky="ew")

        # Sidebar vertical separator
        ctk.CTkFrame(self, width=1, fg_color="#232336", corner_radius=0).grid(
            row=0, column=0, sticky="nse")

        # ---- Content area ----
        self._content = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self.show_view("entries")

    def show_view(self, key: str):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(fg_color="#252540", text_color="#cdd6f4")
            else:
                btn.configure(fg_color="transparent", text_color="#a6adc8")

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

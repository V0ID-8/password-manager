"""Scrollable entry list + inline detail panel."""
import pyperclip
import customtkinter as ctk
from vault import Vault
from ui.widgets import Toast

# Service name → accent color (deterministic by first char)
_ACCENT_PALETTE = [
    "#7c3aed", "#2563eb", "#0891b2", "#059669",
    "#d97706", "#dc2626", "#db2777", "#7c3aed",
]


def _accent_for(name: str) -> str:
    return _ACCENT_PALETTE[ord(name[0].lower()) % len(_ACCENT_PALETTE)] if name else "#313244"


class EntryListView(ctk.CTkFrame):
    def __init__(self, master, vault: Vault, on_navigate, **kwargs):
        super().__init__(master, fg_color="#181825", **kwargs)
        self._vault = vault
        self._on_navigate = on_navigate
        self._selected_id: str | None = None
        self._clipboard_job = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # ---- Left pane ----
        left = ctk.CTkFrame(self, width=290, fg_color="#1e1e2e", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)
        # row 0: header, row 1: search, row 2: list
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Header row
        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(18, 6))
        ctk.CTkLabel(hdr, text="All Entries",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="#cdd6f4").pack(side="left")
        ctk.CTkButton(
            hdr, text="+", width=30, height=30, corner_radius=8,
            font=ctk.CTkFont(size=17, weight="bold"),
            fg_color="#3b4ede", hover_color="#4f5ef0",
            command=lambda: self._on_navigate("add"),
        ).pack(side="right")

        # Search row — row=1, no overlap with header
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        ctk.CTkEntry(
            left, textvariable=self._search_var,
            placeholder_text="🔍  Search entries…", height=34,
            fg_color="#181825", border_color="#313244",
        ).grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        # Scrollable list — row=2
        self._list_frame = ctk.CTkScrollableFrame(
            left, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#313244",
            scrollbar_button_hover_color="#45475a",
        )
        self._list_frame.grid(row=2, column=0, sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

        # Vertical separator
        ctk.CTkFrame(self, width=1, fg_color="#313244", corner_radius=0).grid(
            row=0, column=0, sticky="nse")

        # ---- Right pane (detail) ----
        self._detail_pane = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0)
        self._detail_pane.grid(row=0, column=1, sticky="nsew")
        self._detail_pane.grid_rowconfigure(0, weight=1)
        self._detail_pane.grid_columnconfigure(0, weight=1)
        self._detail_inner: ctk.CTkFrame | None = None

        self._refresh_list()
        self._show_empty_detail()

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        query = self._search_var.get()
        entries = self._vault.search(query)

        if not entries:
            empty = ctk.CTkFrame(self._list_frame, fg_color="transparent")
            empty.pack(fill="x", pady=40, padx=16)
            ctk.CTkLabel(
                empty, text="No entries found",
                font=ctk.CTkFont(size=13, weight="bold"), text_color="#45475a",
            ).pack()
            if not query:
                ctk.CTkLabel(
                    empty, text='Click  +  to add your first entry',
                    font=ctk.CTkFont(size=11), text_color="#313244",
                ).pack(pady=(4, 0))
            return

        for entry in sorted(entries, key=lambda e: e["service"].lower()):
            self._make_card(entry)

    def _make_card(self, entry: dict):
        is_selected = entry["id"] == self._selected_id
        accent = _accent_for(entry["service"])

        card = ctk.CTkFrame(
            self._list_frame, corner_radius=10,
            fg_color="#2a2a3e" if is_selected else "#232336",
            cursor="hand2",
        )
        card.pack(fill="x", padx=10, pady=3)
        card.grid_columnconfigure(1, weight=1)

        # Colored avatar circle
        avatar = ctk.CTkFrame(card, width=36, height=36, corner_radius=10,
                               fg_color=accent)
        avatar.grid(row=0, column=0, rowspan=2, padx=(12, 10), pady=10, sticky="w")
        avatar.grid_propagate(False)
        ctk.CTkLabel(avatar,
                     text=entry["service"][0].upper(),
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#ffffff").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=entry["service"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cdd6f4", anchor="w").grid(
            row=0, column=1, sticky="sw", pady=(10, 1))
        ctk.CTkLabel(card, text=entry["username"] or "—",
                     font=ctk.CTkFont(size=11), text_color="#6c7086",
                     anchor="w").grid(row=1, column=1, sticky="nw", pady=(0, 10))

        # Left accent bar for selected
        if is_selected:
            bar = ctk.CTkFrame(card, width=3, corner_radius=2, fg_color=accent)
            bar.place(relx=0, rely=0.1, relheight=0.8)

        for widget in [card, avatar]:
            widget.bind("<Button-1>", lambda _, eid=entry["id"]: self._select(eid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _, eid=entry["id"]: self._select(eid))
        for grandchild in avatar.winfo_children():
            grandchild.bind("<Button-1>", lambda _, eid=entry["id"]: self._select(eid))

    def _select(self, entry_id: str):
        self._selected_id = entry_id
        self._refresh_list()
        entry = self._vault.get_by_id(entry_id)
        if entry:
            self._show_detail(entry)

    # ------------------------------------------------------------------
    # Detail pane — empty state
    # ------------------------------------------------------------------

    def _show_empty_detail(self):
        if self._detail_inner:
            self._detail_inner.destroy()

        pane = ctk.CTkFrame(self._detail_pane, fg_color="#181825", corner_radius=0)
        pane.grid(row=0, column=0, sticky="nsew")
        pane.grid_rowconfigure(0, weight=1)
        pane.grid_columnconfigure(0, weight=1)
        self._detail_inner = pane

        center = ctk.CTkFrame(pane, fg_color="transparent")
        center.grid(row=0, column=0)

        # Icon placeholder
        icon_frame = ctk.CTkFrame(center, width=72, height=72, corner_radius=20,
                                   fg_color="#1e1e2e")
        icon_frame.pack(pady=(0, 18))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="🔑",
                     font=ctk.CTkFont(size=30)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(center, text="Select an entry",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#45475a").pack()
        ctk.CTkLabel(center, text="Click any entry on the left to view its details.",
                     font=ctk.CTkFont(size=12), text_color="#313244").pack(pady=(6, 0))

    # ------------------------------------------------------------------
    # Detail pane — entry view
    # ------------------------------------------------------------------

    def _show_detail(self, entry: dict):
        if self._detail_inner:
            self._detail_inner.destroy()

        pane = ctk.CTkScrollableFrame(
            self._detail_pane, fg_color="#181825", corner_radius=0,
            scrollbar_button_color="#313244",
            scrollbar_button_hover_color="#45475a",
        )
        pane.grid(row=0, column=0, sticky="nsew")
        pane.grid_columnconfigure(0, weight=1)
        self._detail_inner = pane

        accent = _accent_for(entry["service"])

        # Top accent strip
        ctk.CTkFrame(pane, height=3, corner_radius=0, fg_color=accent).pack(
            fill="x", pady=(0, 0))

        # Title bar
        title_row = ctk.CTkFrame(pane, fg_color="transparent")
        title_row.pack(fill="x", padx=28, pady=(20, 4))

        # Avatar + service name
        name_col = ctk.CTkFrame(title_row, fg_color="transparent")
        name_col.pack(side="left")
        avatar = ctk.CTkFrame(name_col, width=44, height=44, corner_radius=12,
                               fg_color=accent)
        avatar.pack(side="left", padx=(0, 14))
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=entry["service"][0].upper(),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#ffffff").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(name_col, text=entry["service"],
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#cdd6f4").pack(side="left")

        # Action buttons
        action_row = ctk.CTkFrame(title_row, fg_color="transparent")
        action_row.pack(side="right")
        ctk.CTkButton(action_row, text="Edit", width=76, height=34,
                      corner_radius=8, font=ctk.CTkFont(size=12),
                      fg_color="#313244", hover_color="#45475a",
                      command=lambda: self._open_edit(entry)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(action_row, text="Delete", width=76, height=34,
                      corner_radius=8, font=ctk.CTkFont(size=12),
                      fg_color="#3d1515", hover_color="#c0392b", text_color="#f38ba8",
                      command=lambda: self._confirm_delete(entry)).pack(side="left")

        sep = ctk.CTkFrame(pane, height=1, fg_color="#232336")
        sep.pack(fill="x", padx=28, pady=(16, 16))

        toast = Toast(pane)
        toast.pack(padx=28, anchor="w", pady=(0, 8))

        self._build_field(pane, "Username / Email", entry["username"],
                          copyable=True, toast=toast)
        self._build_password_field(pane, entry["password"], toast)
        if entry.get("url"):
            self._build_field(pane, "URL", entry["url"], copyable=True, toast=toast)
        if entry.get("notes"):
            self._build_field(pane, "Notes", entry["notes"])

        # Footer timestamps
        footer = ctk.CTkFrame(pane, fg_color="#1a1a28", corner_radius=10)
        footer.pack(fill="x", padx=28, pady=(16, 28))
        ctk.CTkLabel(footer, text=f"Added  {_fmt_date(entry['created_at'])}",
                     font=ctk.CTkFont(size=11), text_color="#45475a").pack(
            padx=16, pady=(10, 2), anchor="w")
        ctk.CTkLabel(footer, text=f"Updated  {_fmt_date(entry['updated_at'])}",
                     font=ctk.CTkFont(size=11), text_color="#45475a").pack(
            padx=16, pady=(0, 10), anchor="w")

    def _build_field(self, parent, label: str, value: str,
                     copyable: bool = False, toast: Toast | None = None):
        ctk.CTkLabel(parent, text=label.upper(),
                     font=ctk.CTkFont(size=10), text_color="#585b70",
                     anchor="w").pack(fill="x", padx=28, pady=(0, 4))
        row = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=8)
        row.pack(fill="x", padx=28, pady=(0, 16))
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=13),
                     text_color="#cdd6f4", anchor="w", wraplength=440).pack(
            side="left", padx=14, pady=10, expand=True, fill="x")
        if copyable and toast:
            ctk.CTkButton(row, text="Copy", width=58, height=28,
                          corner_radius=6, font=ctk.CTkFont(size=11),
                          fg_color="#313244", hover_color="#45475a",
                          command=lambda v=value: self._copy(v, toast)).pack(
                side="right", padx=8, pady=6)

    def _build_password_field(self, parent, password: str, toast: Toast):
        ctk.CTkLabel(parent, text="PASSWORD",
                     font=ctk.CTkFont(size=10), text_color="#585b70",
                     anchor="w").pack(fill="x", padx=28, pady=(0, 4))
        row = ctk.CTkFrame(parent, fg_color="#1e1e2e", corner_radius=8)
        row.pack(fill="x", padx=28, pady=(0, 16))

        pw_var = ctk.StringVar(value="•" * 16)
        showing = [False]

        ctk.CTkLabel(row, textvariable=pw_var,
                     font=ctk.CTkFont(size=14, family="Courier"),
                     text_color="#cdd6f4", anchor="w").pack(
            side="left", padx=14, pady=10, expand=True, fill="x")

        def toggle():
            showing[0] = not showing[0]
            pw_var.set(password if showing[0] else "•" * 16)
            reveal_btn.configure(text="Hide" if showing[0] else "Show")

        ctk.CTkButton(row, text="Copy", width=58, height=28,
                      corner_radius=6, font=ctk.CTkFont(size=11),
                      fg_color="#313244", hover_color="#45475a",
                      command=lambda: self._copy(password, toast)).pack(
            side="right", padx=(4, 8), pady=6)

        reveal_btn = ctk.CTkButton(row, text="Show", width=58, height=28,
                                   corner_radius=6, font=ctk.CTkFont(size=11),
                                   fg_color="#313244", hover_color="#45475a",
                                   command=toggle)
        reveal_btn.pack(side="right", pady=6)

    def _copy(self, value: str, toast: Toast):
        try:
            pyperclip.copy(value)
            toast.show("Copied! Clears in 15 s", kind="info")
            if self._clipboard_job:
                self.after_cancel(self._clipboard_job)
            self._clipboard_job = self.after(15_000, self._clear_clipboard)
        except Exception:
            toast.show("Could not access clipboard", kind="error")

    def _clear_clipboard(self):
        try:
            pyperclip.copy("")
        except Exception:
            pass
        self._clipboard_job = None

    # ------------------------------------------------------------------
    # Edit / Delete
    # ------------------------------------------------------------------

    def _open_edit(self, entry: dict):
        from ui.add_dialog import AddDialog
        AddDialog(self.winfo_toplevel(), self._vault,
                  existing=entry,
                  on_save=lambda: self._after_mutation(entry["id"]))

    def _confirm_delete(self, entry: dict):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm delete")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus()

        ctk.CTkLabel(dlg, text=f'Delete "{entry["service"]}"?',
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="#cdd6f4").pack(pady=(28, 6))
        ctk.CTkLabel(dlg, text="This action cannot be undone.",
                     font=ctk.CTkFont(size=12), text_color="#6c7086").pack()

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=22)
        ctk.CTkButton(btns, text="Cancel", width=110, height=38,
                      corner_radius=8, fg_color="#313244", hover_color="#45475a",
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Delete", width=110, height=38,
                      corner_radius=8, fg_color="#3d1515", hover_color="#c0392b",
                      text_color="#f38ba8",
                      command=lambda: self._do_delete(entry["id"], dlg)).pack(side="left", padx=8)

    def _do_delete(self, entry_id: str, dlg):
        dlg.destroy()
        self._vault.delete(entry_id)
        self._selected_id = None
        self._refresh_list()
        self._show_empty_detail()

    def _after_mutation(self, entry_id: str):
        self._refresh_list()
        entry = self._vault.get_by_id(entry_id)
        if entry:
            self._show_detail(entry)


def _fmt_date(iso: str) -> str:
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%d %b %Y  %H:%M")
    except Exception:
        return iso

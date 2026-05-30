"""Scrollable entry list + inline detail panel."""
import pyperclip
import customtkinter as ctk
from vault import Vault
from ui.widgets import Toast


class EntryListView(ctk.CTkFrame):
    def __init__(self, master, vault: Vault, on_navigate, **kwargs):
        super().__init__(master, fg_color="#181825", **kwargs)
        self._vault = vault
        self._on_navigate = on_navigate
        self._selected_id: str | None = None
        self._clipboard_job = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # ---- Left pane: search + list ----
        left = ctk.CTkFrame(self, width=280, fg_color="#1e1e2e", corner_radius=0)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew")
        left.grid_propagate(False)
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(left, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(16, 8))
        ctk.CTkLabel(hdr, text="Entries",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#cdd6f4").pack(side="left")
        ctk.CTkButton(hdr, text="+", width=32, height=32,
                      corner_radius=8, font=ctk.CTkFont(size=18),
                      command=lambda: self._on_navigate("add")).pack(side="right")

        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        search = ctk.CTkEntry(left, textvariable=self._search_var,
                              placeholder_text="Search…", height=36)
        search.grid(row=0, column=0, sticky="ew", padx=12, pady=(52, 8))

        self._list_frame = ctk.CTkScrollableFrame(left, fg_color="transparent",
                                                   corner_radius=0)
        self._list_frame.grid(row=1, column=0, sticky="nsew")
        self._list_frame.grid_columnconfigure(0, weight=1)

        # ---- Right pane: detail ----
        self._detail_pane = ctk.CTkFrame(self, fg_color="#181825", corner_radius=0)
        self._detail_pane.grid(row=0, column=1, rowspan=2, sticky="nsew",
                               padx=0, pady=0)
        self._detail_pane.grid_rowconfigure(0, weight=1)
        self._detail_pane.grid_columnconfigure(0, weight=1)
        self._detail_inner: ctk.CTkFrame | None = None

        self._refresh_list()

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def _refresh_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        query = self._search_var.get()
        entries = self._vault.search(query)

        if not entries:
            ctk.CTkLabel(self._list_frame, text="No entries found.",
                         text_color="#585b70",
                         font=ctk.CTkFont(size=13)).pack(pady=24)
            return

        for entry in sorted(entries, key=lambda e: e["service"].lower()):
            self._make_card(entry)

    def _make_card(self, entry: dict):
        is_selected = entry["id"] == self._selected_id
        card = ctk.CTkFrame(
            self._list_frame,
            corner_radius=8,
            fg_color="#313244" if is_selected else "#232336",
            cursor="hand2",
        )
        card.pack(fill="x", padx=8, pady=3)

        ctk.CTkLabel(card, text=entry["service"],
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#cdd6f4", anchor="w").pack(
            padx=12, pady=(8, 1), fill="x")
        ctk.CTkLabel(card, text=entry["username"],
                     font=ctk.CTkFont(size=11),
                     text_color="#a6adc8", anchor="w").pack(
            padx=12, pady=(0, 8), fill="x")

        for widget in (card,):
            widget.bind("<Button-1>", lambda _, eid=entry["id"]: self._select(eid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _, eid=entry["id"]: self._select(eid))

    def _select(self, entry_id: str):
        self._selected_id = entry_id
        self._refresh_list()
        entry = self._vault.get_by_id(entry_id)
        if entry:
            self._show_detail(entry)

    # ------------------------------------------------------------------
    # Detail pane
    # ------------------------------------------------------------------

    def _show_detail(self, entry: dict):
        if self._detail_inner:
            self._detail_inner.destroy()

        pane = ctk.CTkScrollableFrame(self._detail_pane, fg_color="#181825",
                                      corner_radius=0)
        pane.grid(row=0, column=0, sticky="nsew")
        pane.grid_columnconfigure(0, weight=1)
        self._detail_inner = pane

        # Title bar
        title_row = ctk.CTkFrame(pane, fg_color="transparent")
        title_row.pack(fill="x", padx=28, pady=(28, 4))

        ctk.CTkLabel(title_row, text=entry["service"],
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#cdd6f4").pack(side="left")

        action_row = ctk.CTkFrame(title_row, fg_color="transparent")
        action_row.pack(side="right")
        ctk.CTkButton(action_row, text="Edit", width=72, height=32,
                      corner_radius=6, font=ctk.CTkFont(size=12),
                      command=lambda: self._open_edit(entry)).pack(side="left", padx=4)
        ctk.CTkButton(action_row, text="Delete", width=72, height=32,
                      corner_radius=6, font=ctk.CTkFont(size=12),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=lambda: self._confirm_delete(entry)).pack(side="left")

        sep = ctk.CTkFrame(pane, height=1, fg_color="#313244")
        sep.pack(fill="x", padx=28, pady=(8, 20))

        toast = Toast(pane)
        toast.pack(padx=28, anchor="w")

        self._build_field(pane, "Username", entry["username"], copyable=True, toast=toast)
        self._build_password_field(pane, entry["password"], toast)
        if entry.get("url"):
            self._build_field(pane, "URL", entry["url"], copyable=True, toast=toast)
        if entry.get("notes"):
            self._build_field(pane, "Notes", entry["notes"])

        ctk.CTkLabel(pane, text=f"Added {_fmt_date(entry['created_at'])}",
                     font=ctk.CTkFont(size=11), text_color="#585b70").pack(
            padx=28, pady=(24, 0), anchor="w")
        ctk.CTkLabel(pane, text=f"Updated {_fmt_date(entry['updated_at'])}",
                     font=ctk.CTkFont(size=11), text_color="#585b70").pack(
            padx=28, anchor="w", pady=(2, 28))

    def _build_field(self, parent, label: str, value: str,
                     copyable: bool = False, toast: Toast | None = None):
        ctk.CTkLabel(parent, text=label,
                     font=ctk.CTkFont(size=11), text_color="#a6adc8",
                     anchor="w").pack(fill="x", padx=28, pady=(0, 2))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(0, 16))
        ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=13),
                     text_color="#cdd6f4", anchor="w", wraplength=460).pack(
            side="left", expand=True, fill="x")
        if copyable and toast:
            ctk.CTkButton(row, text="Copy", width=56, height=28,
                          corner_radius=6, font=ctk.CTkFont(size=11),
                          command=lambda v=value: self._copy(v, toast)).pack(side="right")

    def _build_password_field(self, parent, password: str, toast: Toast):
        ctk.CTkLabel(parent, text="Password",
                     font=ctk.CTkFont(size=11), text_color="#a6adc8",
                     anchor="w").pack(fill="x", padx=28, pady=(0, 2))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=28, pady=(0, 16))

        pw_var = ctk.StringVar(value="••••••••••••")
        showing = [False]

        lbl = ctk.CTkLabel(row, textvariable=pw_var,
                           font=ctk.CTkFont(size=13, family="Courier"),
                           text_color="#cdd6f4", anchor="w")
        lbl.pack(side="left", expand=True, fill="x")

        def toggle():
            showing[0] = not showing[0]
            pw_var.set(password if showing[0] else "••••••••••••")
            reveal_btn.configure(text="Hide" if showing[0] else "Show")

        reveal_btn = ctk.CTkButton(row, text="Show", width=56, height=28,
                                   corner_radius=6, font=ctk.CTkFont(size=11),
                                   fg_color="#45475a", hover_color="#585b70",
                                   command=toggle)
        reveal_btn.pack(side="right", padx=(4, 0))

        ctk.CTkButton(row, text="Copy", width=56, height=28,
                      corner_radius=6, font=ctk.CTkFont(size=11),
                      command=lambda: self._copy(password, toast)).pack(
            side="right", padx=(0, 4))

    def _copy(self, value: str, toast: Toast):
        try:
            pyperclip.copy(value)
            toast.show("Copied! Clears in 15s", kind="info")
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
        dlg.geometry("360x160")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus()

        ctk.CTkLabel(dlg,
                     text=f'Delete "{entry["service"]}"?',
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(24, 4))
        ctk.CTkLabel(dlg, text="This action cannot be undone.",
                     font=ctk.CTkFont(size=12),
                     text_color="#a6adc8").pack()

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=20)
        ctk.CTkButton(btns, text="Cancel", width=100, height=36,
                      fg_color="#45475a", hover_color="#585b70",
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Delete", width=100, height=36,
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=lambda: self._do_delete(entry["id"], dlg)).pack(side="left", padx=8)

    def _do_delete(self, entry_id: str, dlg: ctk.CTkToplevel):
        dlg.destroy()
        self._vault.delete(entry_id)
        self._selected_id = None
        if self._detail_inner:
            self._detail_inner.destroy()
            self._detail_inner = None
        self._refresh_list()

    def _after_mutation(self, entry_id: str):
        self._refresh_list()
        entry = self._vault.get_by_id(entry_id)
        if entry:
            self._show_detail(entry)


def _fmt_date(iso: str) -> str:
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return iso

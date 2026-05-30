"""Add / Edit entry modal dialog."""
import customtkinter as ctk
from vault import Vault
from generator import generate_password, password_strength
from ui.widgets import StrengthMeter


class AddDialog(ctk.CTkToplevel):
    def __init__(self, master, vault: Vault, on_save,
                 existing: dict | None = None, prefill_password: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self._vault = vault
        self._on_save = on_save
        self._existing = existing

        title = "Edit entry" if existing else "Add entry"
        self.title(title)
        self.geometry("500x560")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        scroll = ctk.CTkScrollableFrame(self, fg_color="#1e1e2e", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(scroll, text=title,
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#cdd6f4").pack(padx=24, pady=(20, 16), anchor="w")

        def field(label, var, placeholder="", show=""):
            ctk.CTkLabel(scroll, text=label, font=ctk.CTkFont(size=11),
                         text_color="#a6adc8", anchor="w").pack(
                fill="x", padx=24, pady=(0, 2))
            entry = ctk.CTkEntry(scroll, textvariable=var,
                                 placeholder_text=placeholder,
                                 show=show, height=38)
            entry.pack(fill="x", padx=24, pady=(0, 10))
            return entry

        self._service_var = ctk.StringVar(value=existing["service"] if existing else "")
        self._user_var = ctk.StringVar(value=existing["username"] if existing else "")
        self._url_var = ctk.StringVar(value=existing.get("url", "") if existing else "")

        field("Service *", self._service_var, "e.g. GitHub")
        field("Username / Email *", self._user_var, "e.g. user@example.com")

        # Password row with generate button
        ctk.CTkLabel(scroll, text="Password *", font=ctk.CTkFont(size=11),
                     text_color="#a6adc8", anchor="w").pack(
            fill="x", padx=24, pady=(0, 2))
        pw_row = ctk.CTkFrame(scroll, fg_color="transparent")
        pw_row.pack(fill="x", padx=24, pady=(0, 4))

        self._pw_var = ctk.StringVar(
            value=existing["password"] if existing else prefill_password
        )
        self._pw_entry = ctk.CTkEntry(pw_row, textvariable=self._pw_var,
                                      show="•", height=38)
        self._pw_entry.pack(side="left", expand=True, fill="x")

        ctk.CTkButton(pw_row, text="👁", width=38, height=38,
                      fg_color="#313244", hover_color="#45475a",
                      command=self._toggle_pw).pack(side="left", padx=(4, 0))
        ctk.CTkButton(pw_row, text="Generate", width=80, height=38,
                      fg_color="#313244", hover_color="#45475a",
                      font=ctk.CTkFont(size=12),
                      command=self._quick_generate).pack(side="left", padx=(4, 0))

        self._strength_meter = StrengthMeter(scroll)
        self._strength_meter.pack(fill="x", padx=24, pady=(0, 8))
        self._pw_var.trace_add("write", self._update_strength)
        self._update_strength()

        field("URL", self._url_var, "https://")

        ctk.CTkLabel(scroll, text="Notes", font=ctk.CTkFont(size=11),
                     text_color="#a6adc8", anchor="w").pack(
            fill="x", padx=24, pady=(0, 2))
        self._notes_text = ctk.CTkTextbox(scroll, height=80, font=ctk.CTkFont(size=13))
        self._notes_text.pack(fill="x", padx=24, pady=(0, 12))
        if existing and existing.get("notes"):
            self._notes_text.insert("1.0", existing["notes"])

        self._error_label = ctk.CTkLabel(scroll, text="",
                                          font=ctk.CTkFont(size=12),
                                          text_color="#f38ba8")
        self._error_label.pack(padx=24, anchor="w")

        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(8, 24))
        ctk.CTkButton(btn_row, text="Cancel", width=90, height=38,
                      fg_color="#45475a", hover_color="#585b70",
                      command=self.destroy).pack(side="right", padx=(8, 0))
        save_text = "Save changes" if existing else "Add entry"
        ctk.CTkButton(btn_row, text=save_text, width=110, height=38,
                      command=self._save).pack(side="right")

    def _toggle_pw(self):
        current = self._pw_entry.cget("show")
        self._pw_entry.configure(show="" if current == "•" else "•")

    def _quick_generate(self):
        pw = generate_password(16)
        self._pw_var.set(pw)
        self._pw_entry.configure(show="")

    def _update_strength(self, *_):
        pw = self._pw_var.get()
        score, label = password_strength(pw)
        self._strength_meter.update_strength(score, label)

    def _save(self):
        service = self._service_var.get().strip()
        username = self._user_var.get().strip()
        password = self._pw_var.get()
        url = self._url_var.get().strip()
        notes = self._notes_text.get("1.0", "end-1c").strip()

        if not service:
            self._error_label.configure(text="Service name is required.")
            return
        if not password:
            self._error_label.configure(text="Password is required.")
            return

        if self._existing:
            self._vault.update(
                self._existing["id"],
                service=service, username=username,
                password=password, url=url, notes=notes,
            )
        else:
            self._vault.add(service, username, password, url, notes)

        self.destroy()
        self._on_save()

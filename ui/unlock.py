"""Master-password unlock / first-run setup screen."""
import os
import customtkinter as ctk
from vault import Vault

VAULT_FILE = "vault.enc"


class UnlockFrame(ctk.CTkFrame):
    def __init__(self, master, vault: Vault, on_unlock, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._vault = vault
        self._on_unlock = on_unlock

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(self, width=400, corner_radius=16, fg_color="#1e1e2e")
        card.grid(row=1, column=0, padx=40, pady=40)
        card.grid_propagate(False)

        # Title
        ctk.CTkLabel(
            card, text="🔐", font=ctk.CTkFont(size=48)
        ).pack(pady=(36, 0))
        ctk.CTkLabel(
            card, text="CrypticRocket",
            font=ctk.CTkFont(size=26, weight="bold"), text_color="#cdd6f4"
        ).pack(pady=(8, 2))

        self._subtitle = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=13), text_color="#a6adc8"
        )
        self._subtitle.pack(pady=(0, 24))
        self._set_subtitle()

        # Password entry with show/hide toggle
        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.pack(padx=32, fill="x")

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(
            pw_row, textvariable=self._pw_var,
            placeholder_text="Master password",
            show="•", height=42, font=ctk.CTkFont(size=14),
        )
        self._pw_entry.pack(side="left", expand=True, fill="x")

        self._show_btn = ctk.CTkButton(
            pw_row, text="👁", width=42, height=42,
            fg_color="#313244", hover_color="#45475a",
            command=self._toggle_show,
        )
        self._show_btn.pack(side="left", padx=(6, 0))

        # Confirm entry (only shown on first run)
        self._confirm_var = ctk.StringVar()
        self._confirm_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._confirm_entry = ctk.CTkEntry(
            self._confirm_frame, textvariable=self._confirm_var,
            placeholder_text="Confirm master password",
            show="•", height=42, font=ctk.CTkFont(size=14),
        )
        self._confirm_entry.pack(fill="x")

        if not os.path.exists(VAULT_FILE):
            self._confirm_frame.pack(padx=32, fill="x", pady=(10, 0))

        # Error label
        self._error_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12),
            text_color="#f38ba8",
        )
        self._error_label.pack(pady=(10, 0))

        # Unlock / Create button
        btn_text = "Create vault" if not os.path.exists(VAULT_FILE) else "Unlock"
        self._unlock_btn = ctk.CTkButton(
            card, text=btn_text, height=42, corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._attempt_unlock,
        )
        self._unlock_btn.pack(padx=32, fill="x", pady=(16, 0))

        ctk.CTkLabel(
            card, text="",
            font=ctk.CTkFont(size=10), text_color="#585b70"
        ).pack(pady=(12, 28))

        # Bind Enter key
        self._pw_entry.bind("<Return>", lambda _: self._attempt_unlock())
        self._confirm_entry.bind("<Return>", lambda _: self._attempt_unlock())
        self._pw_entry.focus()

    def _set_subtitle(self):
        if not os.path.exists(VAULT_FILE):
            self._subtitle.configure(text="Create your master password to get started")
        else:
            self._subtitle.configure(text="Enter your master password to unlock")

    def _toggle_show(self):
        current = self._pw_entry.cget("show")
        new = "" if current == "•" else "•"
        self._pw_entry.configure(show=new)
        self._confirm_entry.configure(show=new)

    def _attempt_unlock(self):
        pw = self._pw_var.get()
        if not pw:
            self._error_label.configure(text="Password cannot be empty.")
            return

        is_first_run = not os.path.exists(VAULT_FILE)

        if is_first_run:
            confirm = self._confirm_var.get()
            if len(pw) < 8:
                self._error_label.configure(text="Master password must be at least 8 characters.")
                return
            if pw != confirm:
                self._error_label.configure(text="Passwords do not match.")
                return

        self._unlock_btn.configure(state="disabled", text="Unlocking…")
        self.after(50, lambda: self._do_unlock(pw))

    def _do_unlock(self, pw: str):
        success = self._vault.unlock(pw)
        if success:
            self._on_unlock()
        else:
            self._unlock_btn.configure(state="normal", text="Unlock")
            self._error_label.configure(text="Wrong master password. Try again.")
            self._pw_var.set("")
            self._pw_entry.focus()

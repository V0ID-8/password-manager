"""Master-password unlock / first-run setup screen."""
import os
import customtkinter as ctk
from vault import Vault

VAULT_FILE = "vault.enc"


class UnlockFrame(ctk.CTkFrame):
    def __init__(self, master, vault: Vault, on_unlock, **kwargs):
        super().__init__(master, fg_color="#11111b", **kwargs)
        self._vault = vault
        self._on_unlock = on_unlock

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        is_first_run = not os.path.exists(VAULT_FILE)
        card_height = 440 if is_first_run else 380

        card = ctk.CTkFrame(
            self, width=420, height=card_height,
            corner_radius=20, fg_color="#1e1e2e",
            border_width=1, border_color="#313244",
        )
        card.grid(row=1, column=0, padx=40, pady=40)
        card.grid_propagate(False)

        # Top accent bar
        accent = ctk.CTkFrame(card, height=4, corner_radius=0, fg_color="#3b4ede")
        accent.place(relx=0, rely=0, relwidth=1)
        # round the top corners of the accent bar by overlapping card corners
        ctk.CTkFrame(card, width=20, height=20, corner_radius=0,
                     fg_color="#3b4ede").place(x=0, y=0)
        ctk.CTkFrame(card, width=20, height=20, corner_radius=0,
                     fg_color="#3b4ede").place(relx=1, y=0, anchor="ne")

        # Icon
        icon_bg = ctk.CTkFrame(card, width=64, height=64, corner_radius=18,
                                fg_color="#252540")
        icon_bg.place(relx=0.5, y=36, anchor="n")
        icon_bg.pack_propagate(False)
        ctk.CTkLabel(icon_bg, text="🔐",
                     font=ctk.CTkFont(size=28)).place(relx=0.5, rely=0.5, anchor="center")

        # Title + subtitle
        ctk.CTkLabel(card, text="CrypticRocket",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color="#cdd6f4").place(relx=0.5, y=118, anchor="n")

        subtitle_text = (
            "Create your master password to get started"
            if is_first_run else
            "Enter your master password to unlock"
        )
        self._subtitle = ctk.CTkLabel(
            card, text=subtitle_text,
            font=ctk.CTkFont(size=12), text_color="#6c7086",
        )
        self._subtitle.place(relx=0.5, y=152, anchor="n")

        # Fields
        field_top = 192

        # Password row
        pw_row = ctk.CTkFrame(card, fg_color="transparent")
        pw_row.place(relx=0.5, y=field_top, anchor="n", relwidth=1)
        pw_row.grid_columnconfigure(0, weight=1)

        self._pw_var = ctk.StringVar()
        self._pw_entry = ctk.CTkEntry(
            pw_row, textvariable=self._pw_var,
            placeholder_text="Master password",
            show="•", height=44, font=ctk.CTkFont(size=14),
            fg_color="#252540", border_color="#313244",
            border_width=1,
        )
        self._pw_entry.grid(row=0, column=0, sticky="ew", padx=(32, 6))

        self._show_btn = ctk.CTkButton(
            pw_row, text="👁", width=44, height=44,
            fg_color="#252540", hover_color="#313244",
            border_width=1, border_color="#313244",
            command=self._toggle_show,
        )
        self._show_btn.grid(row=0, column=1, padx=(0, 32))

        # Confirm row (first run only)
        self._confirm_var = ctk.StringVar()
        self._confirm_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._confirm_entry = ctk.CTkEntry(
            self._confirm_frame, textvariable=self._confirm_var,
            placeholder_text="Confirm master password",
            show="•", height=44, font=ctk.CTkFont(size=14),
            fg_color="#252540", border_color="#313244", border_width=1,
        )
        self._confirm_entry.pack(fill="x", padx=32)

        if is_first_run:
            self._confirm_frame.place(relx=0.5, y=field_top + 58, anchor="n",
                                      relwidth=1)

        # Error label
        err_y = field_top + (116 if is_first_run else 58)
        self._error_label = ctk.CTkLabel(
            card, text="", font=ctk.CTkFont(size=12), text_color="#f38ba8",
        )
        self._error_label.place(relx=0.5, y=err_y, anchor="n")

        # Unlock button
        btn_y = err_y + 28
        btn_text = "Create vault" if is_first_run else "Unlock"
        self._unlock_btn = ctk.CTkButton(
            card, text=btn_text, height=46, corner_radius=10,
            width=356,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#3b4ede", hover_color="#4f5ef0",
            command=self._attempt_unlock,
        )
        self._unlock_btn.place(relx=0.5, y=btn_y, anchor="n")

        # Security badge
        badge_y = card_height - 44
        badge = ctk.CTkFrame(card, fg_color="transparent")
        badge.place(relx=0.5, y=badge_y, anchor="n")
        ctk.CTkLabel(badge, text="AES-256 encrypted  ·  PBKDF2-SHA256",
                     font=ctk.CTkFont(size=10), text_color="#313244").pack()

        self._pw_entry.bind("<Return>", lambda _: self._attempt_unlock())
        self._confirm_entry.bind("<Return>", lambda _: self._attempt_unlock())
        self._pw_entry.focus()

    def _toggle_show(self):
        new = "" if self._pw_entry.cget("show") == "•" else "•"
        self._pw_entry.configure(show=new)
        self._confirm_entry.configure(show=new)

    def _attempt_unlock(self):
        pw = self._pw_var.get()
        if not pw:
            self._error_label.configure(text="Password cannot be empty.")
            return

        is_first_run = not os.path.exists(VAULT_FILE)
        if is_first_run:
            if len(pw) < 8:
                self._error_label.configure(
                    text="Master password must be at least 8 characters.")
                return
            if pw != self._confirm_var.get():
                self._error_label.configure(text="Passwords do not match.")
                return

        self._unlock_btn.configure(state="disabled", text="Unlocking…")
        self.after(50, lambda: self._do_unlock(pw))

    def _do_unlock(self, pw: str):
        if self._vault.unlock(pw):
            self._on_unlock()
        else:
            self._unlock_btn.configure(state="normal", text="Unlock")
            self._error_label.configure(text="Wrong master password. Try again.")
            self._pw_var.set("")
            self._pw_entry.focus()

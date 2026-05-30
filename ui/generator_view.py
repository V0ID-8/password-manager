"""Password generator view."""
import pyperclip
import customtkinter as ctk
from generator import generate_password, password_strength
from ui.widgets import StrengthMeter, Toast


class GeneratorView(ctk.CTkFrame):
    def __init__(self, master, vault, on_navigate, **kwargs):
        super().__init__(master, fg_color="#181825", **kwargs)
        self._vault = vault
        self._on_navigate = on_navigate
        self._clipboard_job = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        content = ctk.CTkScrollableFrame(self, fg_color="#181825", corner_radius=0)
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(content, text="Password Generator",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#cdd6f4").pack(padx=32, pady=(28, 4), anchor="w")
        ctk.CTkLabel(content, text="Generate a secure password using your chosen options.",
                     font=ctk.CTkFont(size=13), text_color="#a6adc8").pack(
            padx=32, anchor="w", pady=(0, 24))

        # ---- Options card ----
        card = ctk.CTkFrame(content, fg_color="#1e1e2e", corner_radius=12)
        card.pack(fill="x", padx=32, pady=(0, 20))
        card.grid_columnconfigure(1, weight=1)

        # Length slider
        ctk.CTkLabel(card, text="Length",
                     font=ctk.CTkFont(size=12), text_color="#a6adc8").grid(
            row=0, column=0, padx=(20, 12), pady=(20, 8), sticky="w")

        self._len_var = ctk.IntVar(value=16)
        self._len_label = ctk.CTkLabel(card, text="16",
                                        font=ctk.CTkFont(size=13, weight="bold"),
                                        text_color="#cdd6f4", width=32)
        self._len_label.grid(row=0, column=2, padx=(8, 20), pady=(20, 8))

        slider = ctk.CTkSlider(card, from_=8, to=64, number_of_steps=56,
                               variable=self._len_var,
                               command=self._on_length_change)
        slider.grid(row=0, column=1, sticky="ew", pady=(20, 8))

        sep = ctk.CTkFrame(card, height=1, fg_color="#313244")
        sep.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16)

        # Character class checkboxes
        self._use_upper = ctk.BooleanVar(value=True)
        self._use_lower = ctk.BooleanVar(value=True)
        self._use_digits = ctk.BooleanVar(value=True)
        self._use_symbols = ctk.BooleanVar(value=True)

        checks = [
            ("Uppercase (A-Z)", self._use_upper),
            ("Lowercase (a-z)", self._use_lower),
            ("Digits (0-9)", self._use_digits),
            ("Symbols (!@#…)", self._use_symbols),
        ]
        check_frame = ctk.CTkFrame(card, fg_color="transparent")
        check_frame.grid(row=2, column=0, columnspan=3, padx=20, pady=16, sticky="ew")
        check_frame.grid_columnconfigure((0, 1), weight=1)

        for i, (label, var) in enumerate(checks):
            ctk.CTkCheckBox(check_frame, text=label, variable=var,
                            font=ctk.CTkFont(size=13)).grid(
                row=i // 2, column=i % 2, sticky="w", pady=4)

        # ---- Generate button ----
        ctk.CTkButton(content, text="Generate password", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      corner_radius=10, command=self._generate).pack(
            fill="x", padx=32, pady=(0, 20))

        # ---- Result area ----
        result_card = ctk.CTkFrame(content, fg_color="#1e1e2e", corner_radius=12)
        result_card.pack(fill="x", padx=32, pady=(0, 12))
        result_card.grid_columnconfigure(0, weight=1)

        self._result_var = ctk.StringVar(value="")
        self._result_entry = ctk.CTkEntry(
            result_card, textvariable=self._result_var,
            state="readonly", height=48,
            font=ctk.CTkFont(size=15, family="Courier"),
            fg_color="#181825",
        )
        self._result_entry.pack(fill="x", padx=16, pady=(16, 8))

        self._strength_meter = StrengthMeter(result_card)
        self._strength_meter.pack(fill="x", padx=16, pady=(0, 12))

        btn_row = ctk.CTkFrame(result_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkButton(btn_row, text="Copy", height=36, corner_radius=8,
                      font=ctk.CTkFont(size=13), command=self._copy).pack(
            side="left", padx=(0, 8))
        ctk.CTkButton(btn_row, text="Save to new entry", height=36, corner_radius=8,
                      fg_color="#313244", hover_color="#45475a",
                      font=ctk.CTkFont(size=13),
                      command=self._save_to_entry).pack(side="left")

        self._toast = Toast(content)
        self._toast.pack(padx=32, anchor="w", pady=(0, 24))

        # Generate one on load
        self._generate()

    def _on_length_change(self, val):
        self._len_label.configure(text=str(int(val)))

    def _generate(self):
        try:
            pw = generate_password(
                length=int(self._len_var.get()),
                use_upper=self._use_upper.get(),
                use_lower=self._use_lower.get(),
                use_digits=self._use_digits.get(),
                use_symbols=self._use_symbols.get(),
            )
        except ValueError as e:
            self._toast.show(str(e), kind="error")
            return
        self._result_var.set(pw)
        score, label = password_strength(pw)
        self._strength_meter.update_strength(score, label)

    def _copy(self):
        pw = self._result_var.get()
        if not pw:
            return
        try:
            pyperclip.copy(pw)
            self._toast.show("Copied! Clears in 15s", kind="info")
            if self._clipboard_job:
                self.after_cancel(self._clipboard_job)
            self._clipboard_job = self.after(15_000, self._clear_clipboard)
        except Exception:
            self._toast.show("Could not access clipboard", kind="error")

    def _clear_clipboard(self):
        try:
            pyperclip.copy("")
        except Exception:
            pass
        self._clipboard_job = None

    def _save_to_entry(self):
        pw = self._result_var.get()
        if not pw:
            self._toast.show("Generate a password first.", kind="error")
            return
        from ui.add_dialog import AddDialog
        AddDialog(self.winfo_toplevel(), self._vault,
                  prefill_password=pw,
                  on_save=lambda: self._on_navigate("entries"))

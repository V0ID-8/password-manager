"""Encrypted vault export / import dialog."""
import os
import shutil
import zipfile
import tempfile
import customtkinter as ctk
from tkinter import filedialog

VAULT_FILE = "vault.enc"
SALT_FILE = "salt.bin"


class ExportImportDialog(ctk.CTkToplevel):
    def __init__(self, master, vault, on_reimport=None, **kwargs):
        super().__init__(master, **kwargs)
        self._vault = vault
        self._on_reimport = on_reimport

        self.title("Export / Import vault")
        self.geometry("420x300")
        self.resizable(False, False)
        self.grab_set()
        self.focus()

        ctk.CTkLabel(self, text="Export / Import",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#cdd6f4").pack(padx=24, pady=(24, 4), anchor="w")
        ctk.CTkLabel(
            self,
            text="The export file contains your encrypted vault and salt.\n"
                 "It is safe to store or transfer — it cannot be decrypted\n"
                 "without your master password.",
            font=ctk.CTkFont(size=12), text_color="#a6adc8", justify="left",
        ).pack(padx=24, anchor="w", pady=(0, 20))

        ctk.CTkButton(self, text="Export vault (save .zip)",
                      height=40, corner_radius=8,
                      command=self._export).pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkButton(self, text="Import vault (restore from .zip)",
                      height=40, corner_radius=8,
                      fg_color="#313244", hover_color="#45475a",
                      command=self._import).pack(fill="x", padx=24)

        self._status = ctk.CTkLabel(self, text="",
                                     font=ctk.CTkFont(size=12),
                                     text_color="#a6adc8")
        self._status.pack(padx=24, pady=(16, 0), anchor="w")

    def _export(self):
        if not os.path.exists(VAULT_FILE):
            self._status.configure(text="No vault to export.", text_color="#f38ba8")
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".zip",
            filetypes=[("Zip archive", "*.zip")],
            initialfile="crypticroket_backup.zip",
        )
        if not path:
            return
        try:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(VAULT_FILE)
                if os.path.exists(SALT_FILE):
                    zf.write(SALT_FILE)
            self._status.configure(text=f"Exported to {os.path.basename(path)}",
                                    text_color="#2ecc71")
        except Exception as e:
            self._status.configure(text=f"Export failed: {e}", text_color="#f38ba8")

    def _import(self):
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("Zip archive", "*.zip")],
        )
        if not path:
            return

        # Confirm overwrite
        dlg = ctk.CTkToplevel(self)
        dlg.title("Confirm import")
        dlg.geometry("360x160")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.focus()

        ctk.CTkLabel(dlg, text="Replace current vault?",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(24, 4))
        ctk.CTkLabel(dlg, text="Your current vault will be overwritten.",
                     font=ctk.CTkFont(size=12), text_color="#a6adc8").pack()

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=20)
        ctk.CTkButton(btns, text="Cancel", width=100, height=36,
                      fg_color="#45475a", hover_color="#585b70",
                      command=dlg.destroy).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Import", width=100, height=36,
                      fg_color="#e67e22", hover_color="#d35400",
                      command=lambda: self._do_import(path, dlg)).pack(side="left", padx=8)

    def _do_import(self, zip_path: str, confirm_dlg: ctk.CTkToplevel):
        confirm_dlg.destroy()
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if VAULT_FILE not in names:
                    self._status.configure(
                        text="Invalid backup: vault.enc not found.", text_color="#f38ba8")
                    return
                # Extract to a temp dir first, then copy
                with tempfile.TemporaryDirectory() as tmp:
                    zf.extractall(tmp)
                    shutil.copy(os.path.join(tmp, VAULT_FILE), VAULT_FILE)
                    if SALT_FILE in names:
                        shutil.copy(os.path.join(tmp, SALT_FILE), SALT_FILE)
            self._status.configure(
                text="Import successful. Please re-lock and unlock to load the new vault.",
                text_color="#2ecc71")
            if self._on_reimport:
                def _finish():
                    self.destroy()
                    self._on_reimport()
                self.after(1500, _finish)
        except Exception as e:
            self._status.configure(text=f"Import failed: {e}", text_color="#f38ba8")

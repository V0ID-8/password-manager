"""CrypticRocket Password Manager — entry point."""
import os
import sys

# Run from project root so salt.bin / vault.enc land next to main.py
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from vault import Vault
from ui.app import App


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    vault = Vault()
    app = App(vault)
    app.mainloop()


if __name__ == "__main__":
    main()

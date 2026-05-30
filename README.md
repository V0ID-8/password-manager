# CrypticRocket Password Manager

A secure, modern desktop password manager built with Python. Your credentials are encrypted with Fernet (AES-128-CBC + HMAC-SHA256) and unlocked by a single master password that is **never stored**.

---

## Security model

| Layer | Implementation |
|---|---|
| Key derivation | PBKDF2HMAC-SHA256, 480 000 iterations, 32-byte random salt |
| Encryption | Fernet authenticated encryption — tampering is detectable |
| Master password | Never written to disk; wrong password → `InvalidToken` |
| Password generation | Python `secrets` module (CSPRNG) |
| Clipboard | Auto-clears after 15 seconds |

---

## Requirements

- Python 3.11+
- pip packages listed in `requirements.txt`

---

## Install

```bash
# Clone the repo
git clone https://github.com/V0ID-8/password_manager.git
cd password_manager

# Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Run

```bash
python main.py
```

On **first launch** you will be asked to set your master password. This creates `vault.enc` and `salt.bin` in the project directory — both are excluded from version control via `.gitignore`.

On **subsequent launches** enter your master password to unlock the vault.

---

## Features

- Master password gate (first-run setup + unlock)
- Add, edit, delete credential entries (service, username, password, URL, notes)
- Search by service name or username (partial, case-insensitive)
- Password reveal on demand — hidden by default
- Copy password to clipboard with auto-clear after 15 seconds
- Cryptographically secure password generator (choose length and character classes)
- Password strength meter
- Auto-lock after 5 minutes of inactivity
- Encrypted vault export / import

---

## Screenshots

<!-- Add screenshots here after first run -->

---

## License

MIT

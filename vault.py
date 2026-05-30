import json
import os
import uuid
from datetime import datetime, timezone
from cryptography.fernet import InvalidToken

from crypto import encrypt, decrypt, load_or_create_salt, derive_key

VAULT_FILE = "vault.enc"


class Vault:
    def __init__(self):
        self._entries: list[dict] = []
        self._key: bytes | None = None

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def unlock(self, master_password: str) -> bool:
        """Derive key and load vault. Returns True on success."""
        salt = load_or_create_salt()
        key = derive_key(master_password, salt)

        if not os.path.exists(VAULT_FILE):
            # First run — initialise an empty vault with this password.
            self._key = key
            self._entries = []
            self._save()
            return True

        try:
            raw = decrypt(open(VAULT_FILE, "rb").read(), key)
            self._entries = json.loads(raw.decode("utf-8"))
            self._key = key
            return True
        except (InvalidToken, json.JSONDecodeError):
            return False

    def lock(self):
        self._key = None
        self._entries = []

    @property
    def is_unlocked(self) -> bool:
        return self._key is not None

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(
        self,
        service: str,
        username: str,
        password: str,
        url: str = "",
        notes: str = "",
    ) -> dict:
        now = _now()
        entry = {
            "id": str(uuid.uuid4()),
            "service": service.strip(),
            "username": username.strip(),
            "password": password,
            "url": url.strip(),
            "notes": notes.strip(),
            "created_at": now,
            "updated_at": now,
        }
        self._entries.append(entry)
        self._save()
        return entry

    def update(self, entry_id: str, **fields) -> dict:
        entry = self._get(entry_id)
        allowed = {"service", "username", "password", "url", "notes"}
        for k, v in fields.items():
            if k in allowed:
                entry[k] = v
        entry["updated_at"] = _now()
        self._save()
        return entry

    def delete(self, entry_id: str) -> None:
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        self._save()

    def search(self, query: str) -> list[dict]:
        q = query.lower().strip()
        if not q:
            return list(self._entries)
        return [
            e for e in self._entries
            if q in e["service"].lower() or q in e["username"].lower()
        ]

    def all_entries(self) -> list[dict]:
        return list(self._entries)

    def get_by_id(self, entry_id: str) -> dict | None:
        for e in self._entries:
            if e["id"] == entry_id:
                return e
        return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get(self, entry_id: str) -> dict:
        entry = self.get_by_id(entry_id)
        if entry is None:
            raise KeyError(f"No entry with id {entry_id!r}")
        return entry

    def _save(self):
        if self._key is None:
            raise RuntimeError("Vault is locked")
        data = json.dumps(self._entries, ensure_ascii=False).encode("utf-8")
        with open(VAULT_FILE, "wb") as f:
            f.write(encrypt(data, self._key))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------------------------------------------------------------
# Quick smoke test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile, shutil

    orig_dir = os.getcwd()
    tmp = tempfile.mkdtemp()
    os.chdir(tmp)

    try:
        v = Vault()
        assert v.unlock("test-master"), "First unlock should succeed"

        e1 = v.add("GitHub", "talal", "s3cr3t!", url="https://github.com")
        e2 = v.add("Gmail", "talal@gmail.com", "hunter2")

        assert len(v.all_entries()) == 2
        print("  [OK] add two entries")

        results = v.search("git")
        assert len(results) == 1 and results[0]["service"] == "GitHub"
        print("  [OK] search by service name")

        v.update(e1["id"], password="n3w-p@ss")
        reloaded_entry = v.get_by_id(e1["id"])
        assert reloaded_entry["password"] == "n3w-p@ss"
        print("  [OK] update entry")

        v.delete(e2["id"])
        assert len(v.all_entries()) == 1
        print("  [OK] delete entry")

        # Reload from disk with correct password
        v2 = Vault()
        assert v2.unlock("test-master"), "Reload should succeed"
        assert len(v2.all_entries()) == 1
        print("  [OK] vault persists across reload")

        # Wrong password
        v3 = Vault()
        assert not v3.unlock("wrong"), "Wrong password should fail"
        print("  [OK] wrong password rejected")

        print("All vault checks passed.")
    finally:
        os.chdir(orig_dir)
        shutil.rmtree(tmp, ignore_errors=True)

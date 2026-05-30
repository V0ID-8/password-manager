import math
import secrets
import string


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Generate a cryptographically secure password.

    Guarantees at least one character from every enabled class, then fills
    the remainder from the combined pool, then shuffles with secrets.SystemRandom
    so position of the guaranteed chars is not predictable.
    """
    pool = ""
    required_pools: list[str] = []

    if use_upper:
        pool += string.ascii_uppercase
        required_pools.append(string.ascii_uppercase)
    if use_lower:
        pool += string.ascii_lowercase
        required_pools.append(string.ascii_lowercase)
    if use_digits:
        pool += string.digits
        required_pools.append(string.digits)
    if use_symbols:
        pool += string.punctuation
        required_pools.append(string.punctuation)

    if not pool:
        raise ValueError("At least one character class must be selected.")

    if length < len(required_pools):
        raise ValueError(
            f"Password length ({length}) is shorter than the number of "
            f"required character classes ({len(required_pools)})."
        )

    chars = [secrets.choice(p) for p in required_pools]
    chars += [secrets.choice(pool) for _ in range(length - len(chars))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def password_strength(pw: str) -> tuple[int, str]:
    """
    Return (score, label) where score is 0-4.

    Scoring factors: length, presence of each character class, estimated entropy.
    """
    if not pw:
        return 0, "None"

    has_lower = any(c in string.ascii_lowercase for c in pw)
    has_upper = any(c in string.ascii_uppercase for c in pw)
    has_digit = any(c in string.digits for c in pw)
    has_symbol = any(c in string.punctuation for c in pw)

    pool_size = (
        (26 if has_lower else 0)
        + (26 if has_upper else 0)
        + (10 if has_digit else 0)
        + (32 if has_symbol else 0)
    )
    entropy = math.log2(pool_size ** len(pw)) if pool_size > 0 else 0

    class_count = sum([has_lower, has_upper, has_digit, has_symbol])

    if entropy < 28 or len(pw) < 6:
        score, label = 0, "Very Weak"
    elif entropy < 36 or class_count < 2:
        score, label = 1, "Weak"
    elif entropy < 60 or class_count < 3:
        score, label = 2, "Fair"
    elif entropy < 80 or len(pw) < 12:
        score, label = 3, "Strong"
    else:
        score, label = 4, "Very Strong"

    return score, label


if __name__ == "__main__":
    print("Running generator checks...")

    for _ in range(20):
        pw = generate_password(16, use_upper=True, use_lower=True, use_digits=True, use_symbols=True)
        assert any(c in string.ascii_uppercase for c in pw), "Missing uppercase"
        assert any(c in string.ascii_lowercase for c in pw), "Missing lowercase"
        assert any(c in string.digits for c in pw), "Missing digit"
        assert any(c in string.punctuation for c in pw), "Missing symbol"
        assert len(pw) == 16
    print("  [OK] 20x length-16 all-class passwords: correct length and classes")

    pw_alpha = generate_password(12, use_upper=True, use_lower=True, use_digits=False, use_symbols=False)
    assert all(c in string.ascii_letters for c in pw_alpha)
    print("  [OK] alpha-only password contains no digits or symbols")

    s0, _ = password_strength("")
    assert s0 == 0
    s4, lbl = password_strength("X#k9!mP2@nQ7$rW5")
    assert s4 >= 3, f"Expected strong, got {lbl}"
    print(f"  [OK] strength scoring: strong password scored {s4}/4 ({lbl})")

    print("All generator checks passed.")

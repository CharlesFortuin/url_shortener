ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)
CHAR_TO_VAL = {char: idx for idx, char in enumerate(ALPHABET)}

ID_OFFSET = 10_000_000


def encode(num: int) -> str:
    """Convert a non-negative base-10 integer into a Base62 string."""
    if num < 0:
        raise ValueError("Cannot encode a negative integer.")
    if num == 0:
        return ALPHABET[0]

    chars: list[str] = []
    while num > 0:
        num, remainder = divmod(num, BASE)
        chars.append(ALPHABET[remainder])

    return "".join(reversed(chars))


def decode(short_code: str) -> int:
    """Convert a Base62 string back into its base-10 integer."""
    if not short_code:
        raise ValueError("Cannot decode an empty string.")

    num = 0
    for char in short_code:
        if char not in CHAR_TO_VAL:
            raise ValueError(f"Invalid Base62 character: '{char}'")
        num = num * BASE + CHAR_TO_VAL[char]

    return num
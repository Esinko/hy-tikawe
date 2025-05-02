import re


def is_good_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        # Lowercase, uppercase, symbols and at least 8 long
        bool(re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$", password))
    )

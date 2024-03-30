import string


def is_hex_string(s: str, check_prefix: bool = True):
    if check_prefix and not s.startswith("0x"):
        return False

    string_to_check = s if not check_prefix else s[2:]

    return s.isalnum() and all(c in string.hexdigits for c in string_to_check)

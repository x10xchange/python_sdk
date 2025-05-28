import random


def generate_nonce() -> int:
    """
    Generates a nonce for use in StarkEx transactions.

    Returns:
        int: A random nonce.
    """
    return random.randint(0, 2**64 - 1)

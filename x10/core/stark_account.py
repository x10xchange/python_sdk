from typing import Tuple

from fast_stark_crypto import sign

from x10.utils.string import is_hex_string


class StarkPerpetualAccount:
    __vault: int
    __private_key: int
    __public_key: int

    def __init__(self, vault: int | str, private_key: str, public_key: str, api_key: str):
        assert is_hex_string(private_key)
        assert is_hex_string(public_key)

        if isinstance(vault, str):
            vault = int(vault)
        elif isinstance(vault, int):
            self.__vault = vault
        else:
            raise ValueError("Invalid vault type")

        self.__vault = vault
        self.__private_key = int(private_key, base=16)
        self.__public_key = int(public_key, base=16)
        self.__api_key = api_key

    @property
    def vault(self):
        return self.__vault

    @property
    def public_key(self):
        return self.__public_key

    @property
    def api_key(self):
        return self.__api_key

    def sign(self, msg_hash: int) -> Tuple[int, int]:
        return sign(private_key=self.__private_key, msg_hash=msg_hash)

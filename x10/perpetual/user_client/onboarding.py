import re
from dataclasses import dataclass

from eth_account import Account
from eth_account.messages import SignableMessage, encode_typed_data

from vendor.starkware.crypto import signature as stark_sign


@dataclass
class StarkKeyPair:
    private: int
    public: int

    @property
    def public_hex(self) -> str:
        return hex(self.public)

    @property
    def private_hex(self) -> str:
        return hex(self.private)


def get_key_derivation_struct_to_sign(
    account_index: int, address: str, signing_domain: str = "x10.exchange"
) -> SignableMessage:
    primary_type = "AccountCreation"
    domain = {"name": signing_domain}
    message = {
        "accountIndex": account_index,
        "wallet": address,
        "tosAccepted": True,
    }
    types = {
        "EIP712Domain": [
            {"name": "name", "type": "string"},
        ],
        "AccountCreation": [
            {"name": "accountIndex", "type": "int8"},
            {"name": "wallet", "type": "address"},
            {"name": "tosAccepted", "type": "bool"},
        ],
    }
    structured_data = {
        "types": types,
        "domain": domain,
        "primaryType": primary_type,
        "message": message,
    }
    return encode_typed_data(full_message=structured_data)


def get_private_key_from_eth_signature(eth_signature: str) -> int:
    eth_sig_truncated = re.sub("^0x", "", eth_signature)
    r = eth_sig_truncated[:64]
    return stark_sign.grind_key(int(r, 16), stark_sign.EC_ORDER)


def get_l2_keys_from_l1_account(account: Account, account_index: int) -> StarkKeyPair:
    struct = get_key_derivation_struct_to_sign(account_index=account_index, address=account.address)  # type: ignore
    s = account.sign_message(struct)
    private = get_private_key_from_eth_signature(s.signature.hex())
    public = stark_sign.private_to_stark_key(private)
    return StarkKeyPair(private=private, public=public)

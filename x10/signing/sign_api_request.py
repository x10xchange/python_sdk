from datetime import datetime, timezone
from typing import Callable

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount

from utils.date import utc_now


def sign_api_request(request_path: str, get_l1_private_key: Callable[[], str]) -> tuple[str, str]:
    signing_account: LocalAccount = Account.from_key(get_l1_private_key())
    now = utc_now()
    now_as_string = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    l1_message = f"{request_path}@{now_as_string}".encode(encoding="utf-8")
    encoded_l1_message = encode_defunct(l1_message)
    l1_signature = signing_account.sign_message(encoded_l1_message)

    return l1_signature.signature.hex(), now_as_string

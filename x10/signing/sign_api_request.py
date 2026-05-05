from datetime import datetime, timezone
from typing import Callable, NamedTuple

from core.types import SignMessageCallback
from eth_account import Account
from eth_account.messages import SignableMessage, encode_defunct
from eth_account.signers.local import LocalAccount
from utils.date import utc_now


class RequestSignature(NamedTuple):
    value: str
    time: str


# FIXME: Add test
def sign_api_request(request_path: str, sign_message: SignMessageCallback) -> RequestSignature:
    now = utc_now()
    now_as_string = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    l1_message = f"{request_path}@{now_as_string}".encode(encoding="utf-8")
    encoded_l1_message = encode_defunct(l1_message)
    l1_signature = sign_message(encoded_l1_message)

    return RequestSignature(l1_signature, now_as_string)

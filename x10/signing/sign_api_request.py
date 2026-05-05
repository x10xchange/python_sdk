from typing import NamedTuple

from eth_account.messages import encode_defunct

from x10.core.types import SignMessageCallback
from x10.utils.date import utc_now


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

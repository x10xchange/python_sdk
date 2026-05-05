from eth_account import Account
from eth_account.messages import SignableMessage
from eth_account.signers.local import LocalAccount
from freezegun import freeze_time
from hamcrest import assert_that, equal_to

from x10.signing.onboarding import (
    RequestSignature,
    get_l2_keys_from_l1_account,
    get_onboarding_payload,
    sign_api_request,
)
from x10.utils.date import utc_now

# All known values from authentication service tests are used.
KNOWN_L2_PRIVATE_KEY = "0x7dbb2c8651cc40e1d0d60b45eb52039f317a8aa82798bda52eee272136c0c44"
KNOWN_L2_PUBLIC_KEY = "0x78298687996aff29a0bbcb994e1305db082d084f85ec38bb78c41e6787740ec"


@freeze_time("2024-01-05 01:08:56.860694")
def test_sign_api_request(get_eth_private_key):
    local_account: LocalAccount = Account.from_key(get_eth_private_key())
    signature = sign_api_request("/action", lambda msg: local_account.sign_message(msg).signature.hex())

    assert_that(
        signature,
        equal_to(
            RequestSignature(
                "f4e4e9aaf2014a3651dfafec63854e4dfd486dcc10e77f56b330e9942630fde03588e43d6c022f8513c1e4cf211e670c3134d3cfdf1bd61b570d2588bfb9fc921b",  # noqa: E501
                "2024-01-05T01:08:56Z",
            )
        ),
    )


@freeze_time("2024-07-30 16:01:02.000000")
def test_onboarding_object_generation(get_eth_private_key):
    l1_account = Account.from_key(get_eth_private_key())

    def sign_message(msg: SignableMessage) -> str:
        return l1_account.sign_message(msg).signature.hex()

    key_pair = get_l2_keys_from_l1_account(
        account_index=0, account_address=l1_account.address, signing_domain="x10.exchange", sign_message=sign_message
    )

    payload = get_onboarding_payload(
        account_address=l1_account.address,
        time=utc_now(),
        host="host",
        key_pair=key_pair,
        signing_domain="x10.exchange",
        sign_message=sign_message,
    ).to_json()

    assert_that(
        payload,
        equal_to(
            {
                "l1Signature": "9a59eb699eb58f2ec975455f33dd7205c8a569f7b6d7647c25b71e7ab7eec3d30f2b8c9038f06f077167eb90e0c002602e4ecbab180fad4b2c91d2259883e6571c",  # noqa: E501
                "l2Key": KNOWN_L2_PUBLIC_KEY,
                "l2Signature": {
                    "r": "0x70881694c59c7212b1a47fbbc07df4d32678f0326f778861ec3a2a5dbc09157",
                    "s": "0x558805193faa5d780719cba5f699ae1c888eec1fee23da4215fdd94a744d2cb",
                },
                "accountCreation": {
                    "accountIndex": 0,
                    "wallet": "0x2c12f074766f5eF9c5300ca8C85d06fBa605C59f",
                    "tosAccepted": True,
                    "time": "2024-07-30T16:01:02Z",
                    "action": "REGISTER",
                    "host": "host",
                },
                "referralCode": None,
            }
        ),
    )


def test_known_l2_accounts(get_eth_private_key):
    local_account: LocalAccount = Account.from_key(get_eth_private_key())
    derived_keys = get_l2_keys_from_l1_account(
        account_index=0,
        account_address=local_account.address,
        signing_domain="x10.exchange",
        sign_message=lambda msg: local_account.sign_message(msg).signature.hex(),
    )

    assert_that(derived_keys.private_hex, equal_to(KNOWN_L2_PRIVATE_KEY))
    assert_that(derived_keys.public_hex, equal_to(KNOWN_L2_PUBLIC_KEY))

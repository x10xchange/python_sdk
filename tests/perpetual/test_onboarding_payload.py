import datetime

from eth_account import Account

from x10.perpetual.user_client.onboarding import get_l2_keys_from_l1_account


def test_onboarding_object_generation():
    # all known values from authentication service tests
    from x10.perpetual.user_client.onboarding import get_onboarding_payload

    known_private_key = "50c8e358cc974aaaa6e460641e53f78bdc550fd372984aa78ef8fd27c751e6f4"
    known_l2_public_key = "0x78298687996aff29a0bbcb994e1305db082d084f85ec38bb78c41e6787740ec"

    l1_account = Account.from_key(known_private_key)
    key_pair = get_l2_keys_from_l1_account(l1_account=l1_account, account_index=0, signing_domain="x10.exchange")

    payload = get_onboarding_payload(
        account=l1_account,
        time=datetime.datetime(
            year=2024,
            month=7,
            day=30,
            hour=16,
            minute=1,
            second=2,
            tzinfo=datetime.timezone.utc,
        ),
        host="host",
        key_pair=key_pair,
        signing_domain="x10.exchange",
    ).to_json()

    assert (
        "0x" + payload["l1Signature"]
        == "0x9a59eb699eb58f2ec975455f33dd7205c8a569f7b6d7647c25b71e7ab7eec3d30f2b8c9038f06f077167eb90e0c002602e4ecbab180fad4b2c91d2259883e6571c"  # noqa: E501
    )

    assert payload["l2Key"] == known_l2_public_key
    assert payload["l2Signature"]["r"] == "0x70881694c59c7212b1a47fbbc07df4d32678f0326f778861ec3a2a5dbc09157"
    assert payload["l2Signature"]["s"] == "0x558805193faa5d780719cba5f699ae1c888eec1fee23da4215fdd94a744d2cb"
    assert payload["accountCreation"]["time"] == "2024-07-30T16:01:02Z"
    assert payload["accountCreation"]["action"] == "REGISTER"
    assert payload["accountCreation"]["tosAccepted"] is True

from eth_account import Account


def test_known_l2_accounts():
    from x10.perpetual.user_client.onboarding import get_l2_keys_from_l1_account

    known_private_key = "50c8e358cc974aaaa6e460641e53f78bdc550fd372984aa78ef8fd27c751e6f4"
    known_l2_private_key = "0x7dbb2c8651cc40e1d0d60b45eb52039f317a8aa82798bda52eee272136c0c44"
    known_l2_public_key = "0x78298687996aff29a0bbcb994e1305db082d084f85ec38bb78c41e6787740ec"

    derived_keys = get_l2_keys_from_l1_account(Account.from_key(known_private_key), 0, signing_domain="x10.exchange")
    assert derived_keys.private_hex == known_l2_private_key
    assert derived_keys.public_hex == known_l2_public_key

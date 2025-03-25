import re
from dataclasses import dataclass
from datetime import datetime, timezone

from eth_account.messages import SignableMessage, encode_typed_data
from eth_account.signers.local import LocalAccount

from vendor.starkware.crypto import signature as stark_sign
from x10.perpetual.accounts import AccountModel
from x10.utils.model import X10BaseModel

register_action = "REGISTER"
sub_account_action = "CREATE_SUB_ACCOUNT"


class OnboardedClientModel(X10BaseModel):
    l1_address: str
    default_account: AccountModel


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


@dataclass
class AccountRegistration:
    account_index: int
    wallet: str
    tos_accepted: bool
    time: datetime
    action: str

    def __post_init__(self):
        self.time_string = self.time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_signable_message(self, signing_domain) -> SignableMessage:
        domain = {"name": signing_domain}

        message = {
            "accountIndex": self.account_index,
            "wallet": self.wallet,
            "tosAccepted": self.tos_accepted,
            "time": self.time_string,
            "action": self.action,
        }
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
            ],
            "AccountRegistration": [
                {"name": "accountIndex", "type": "int8"},
                {"name": "wallet", "type": "address"},
                {"name": "tosAccepted", "type": "bool"},
                {"name": "time", "type": "string"},
                {"name": "action", "type": "string"},
            ],
        }
        primary_type = "AccountRegistration"
        structured_data = {
            "types": types,
            "domain": domain,
            "primaryType": primary_type,
            "message": message,
        }
        return encode_typed_data(full_message=structured_data)

    def to_json(self):
        return {
            "accountIndex": self.account_index,
            "wallet": self.wallet,
            "tosAccepted": self.tos_accepted,
            "time": self.time_string,
            "action": self.action,
        }


@dataclass
class SubAccountOnboardingPayload:
    l2_key: int
    l2_r: int
    l2_s: int
    account_registration: AccountRegistration
    description: str

    def to_json(self):
        return {
            "l2Key": hex(self.l2_key),
            "l2Signature": {
                "r": hex(self.l2_r),
                "s": hex(self.l2_s),
            },
            "accountCreation": self.account_registration.to_json(),
            "description": self.description,
        }


@dataclass
class OnboardingPayLoad:
    l1_signature: str
    l2_key: int
    l2_r: int
    l2_s: int
    account_registration: AccountRegistration
    referral_code: str | None = None

    def to_json(self):
        return {
            "l1Signature": self.l1_signature,
            "l2Key": hex(self.l2_key),
            "l2Signature": {
                "r": hex(self.l2_r),
                "s": hex(self.l2_s),
            },
            "accountCreation": self.account_registration.to_json(),
            "referralCode": self.referral_code,
        }


def get_registration_struct_to_sign(
    account_index: int, address: str, timestamp: datetime, action: str
) -> AccountRegistration:
    return AccountRegistration(
        account_index=account_index,
        wallet=address,
        tos_accepted=True,
        time=timestamp,
        action=action,
    )


def get_key_derivation_struct_to_sign(account_index: int, address: str, signing_domain: str) -> SignableMessage:
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


def get_l2_keys_from_l1_account(l1_account: LocalAccount, account_index: int, signing_domain: str) -> StarkKeyPair:
    struct = get_key_derivation_struct_to_sign(
        account_index=account_index,
        address=l1_account.address,
        signing_domain=signing_domain,
    )
    s = l1_account.sign_message(struct)
    private = get_private_key_from_eth_signature(s.signature.hex())
    public = stark_sign.private_to_stark_key(private)
    return StarkKeyPair(private=private, public=public)


def get_onboarding_payload(
    account: LocalAccount,
    signing_domain: str,
    key_pair: StarkKeyPair,
    time: datetime | None = None,
    referral_code: str | None = None,
) -> OnboardingPayLoad:
    if time is None:
        time = datetime.now(timezone.utc)

    registration_payload = get_registration_struct_to_sign(
        account_index=0, address=account.address, timestamp=time, action=register_action
    )
    l1_signature = account.sign_message(
        registration_payload.to_signable_message(signing_domain=signing_domain)
    ).signature.hex()
    l2_message = stark_sign.pedersen_hash(int(account.address, 16), key_pair.public)
    l2_r, l2_s = stark_sign.sign(msg_hash=l2_message, priv_key=key_pair.private)
    onboarding_payload = OnboardingPayLoad(
        l1_signature=l1_signature,
        l2_key=key_pair.public,
        l2_r=l2_r,
        l2_s=l2_s,
        account_registration=registration_payload,
        referral_code=referral_code,
    )
    return onboarding_payload


def get_sub_account_creation_payload(
    account_index: int, l1_address: str, key_pair: StarkKeyPair, description: str, time: datetime | None = None
):
    if time is None:
        time = datetime.now(timezone.utc)

    registration_payload = get_registration_struct_to_sign(
        account_index=account_index,
        address=l1_address,
        timestamp=time,
        action=sub_account_action,
    )

    l2_message = stark_sign.pedersen_hash(int(l1_address, 16), key_pair.public)
    l2_r, l2_s = stark_sign.sign(msg_hash=l2_message, priv_key=key_pair.private)

    return SubAccountOnboardingPayload(
        l2_key=key_pair.public,
        l2_r=l2_r,
        l2_s=l2_s,
        account_registration=registration_payload,
        description=description,
    )

from dataclasses import dataclass


@dataclass
class EndpointConfig:
    api_base_url: str
    stream_url: str


TESTNET_CONFIG = EndpointConfig(
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
)

MAINNET_CONFIG = EndpointConfig(
    api_base_url="https://api.x10.exchange/api/v1",
    stream_url="wss://api.x10.exchange/stream.x10.exchange/v1",
)

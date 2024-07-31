from dataclasses import dataclass


@dataclass
class EndpointConfig:
    chain_rpc_url: str
    api_base_url: str
    stream_url: str


TESTNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://rpc.sepolia.org",
    api_base_url="https://api.testnet.x10.exchange/api/v1",
    stream_url="wss://api.testnet.x10.exchange/stream.x10.exchange/v1",
)

MAINNET_CONFIG = EndpointConfig(
    chain_rpc_url="https://cloudflare-eth.com",
    api_base_url="https://api.prod.x10.exchange/api/v1",
    stream_url="wss://api.prod.x10.exchange/stream.x10.exchange/v1",
)

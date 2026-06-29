from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


# FIXME: Not a model? Is it really used?
@dataclass(frozen=True)
class StreamMessageEnvelope(Generic[T]):
    type: str
    data: T
    ts: int
    seq: int
    subscription: str
    error: str | None = None

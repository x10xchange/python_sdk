from typing import Callable, TypeAlias, TypeVar

from eth_account.messages import SignableMessage

# FIXME: Move to ...?
SignMessageCallback: TypeAlias = Callable[[SignableMessage], str]

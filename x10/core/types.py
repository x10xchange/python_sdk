from typing import Callable, TypeAlias

from eth_account.messages import SignableMessage

# FIXME: Move to ...?
SignMessageCallback: TypeAlias = Callable[[SignableMessage], str]

from typing import Tuple

from brownie.network.account import ClefAccount
from enforce_typing import enforce_types

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.utils import sign_with_clef, sign_with_key


@enforce_types
def sign_message(wallet, msg: str, provider_uri: str) -> Tuple[str, str]:
    nonce = DataServiceProvider.get_nonce(wallet.address, provider_uri)
    print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")

    if isinstance(wallet, ClefAccount):
        return nonce, str(sign_with_clef(f"{msg}{nonce}", wallet))

    return nonce, str(sign_with_key(f"{msg}{nonce}", wallet.private_key))

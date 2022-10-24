#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from brownie import network
from enforce_typing import enforce_types
from eth_account.datastructures import SignedMessage
from eth_account.messages import SignableMessage
from web3.main import Web3

from ocean_lib.example_config import NETWORK_IDS
from ocean_lib.web3_internal.utils import (
    private_key_to_address,
    private_key_to_public_key,
)

logger = logging.getLogger(__name__)


class Wallet:

    """
    The wallet is responsible for signing transactions and messages by using an account's
    private key.

    The use of this wallet allows Ocean tools to send rawTransactions which keeps the user
    key and password safe and they are never sent outside. Another advantage of this is that
    we can interact directly with remote network nodes without having to run a local parity
    node since we only send the raw transaction hash so the user info is safe.

    Usage:
    ```python
    wallet = Wallet(
        ocean.web3,
        private_key=private_key,
    )
    ```

    """

    _last_tx_count = dict()

    @enforce_types
    def __init__(
        self,
        web3: Web3,
        private_key: str,
    ) -> None:
        """Initialises Wallet object."""
        assert private_key, "private_key is required."

        self.web3 = web3
        self._last_tx_count.clear()

        self.private_key = private_key
        self._address = private_key_to_address(self.private_key)

        self.network = NETWORK_IDS[web3.eth.chain_id]
        self.add_to_network()

    def add_to_network(self):
        previously_active = network.show_active()
        if previously_active != self.network:
            if network.is_connected():
                network.disconnect()

            network.connect(self.network)
            network.accounts.add(self.private_key)
        else:
            network.accounts.add(self.private_key)

    @property
    @enforce_types
    def address(self) -> str:
        return self._address

    @property
    @enforce_types
    def key(self) -> str:
        return self.private_key

    @enforce_types
    def validate(self) -> bool:
        account = self.web3.eth.account.from_key(self.private_key)
        return account.address == self._address

    @enforce_types
    def sign(self, msg_hash: SignableMessage) -> SignedMessage:
        """Sign a transaction."""
        account = self.web3.eth.account.from_key(self.private_key)
        return account.sign_message(msg_hash)

    @enforce_types
    def keys_str(self) -> str:
        s = []
        s += [f"address: {self.address}"]
        if self.private_key is not None:
            s += [f"private key: {self.private_key}"]
            s += [f"public key: {private_key_to_public_key(self.private_key)}"]
        s += [""]
        return "\n".join(s)

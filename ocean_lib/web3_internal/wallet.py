#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
from typing import Dict, Optional, Union

from enforce_typing import enforce_types
from eth_account.datastructures import SignedMessage
from eth_account.messages import SignableMessage
from hexbytes.main import HexBytes
from ocean_lib.web3_internal.constants import ENV_MAX_GAS_PRICE, MIN_GAS_PRICE
from ocean_lib.web3_internal.utils import (
    private_key_to_address,
    private_key_to_public_key,
)
from web3.main import Web3

logger = logging.getLogger(__name__)


@enforce_types
class Wallet:

    """
    The wallet is responsible for signing transactions and messages by using an account's
    private key.

    The private key is always read from the encrypted keyfile and is never saved in memory beyond
    the life span of the signing function.

    The use of this wallet allows Ocean tools to send rawTransactions which keeps the user
    key and password safe and they are never sent outside. Another advantage of this is that
    we can interact directly with remote network nodes without having to run a local parity
    node since we only send the raw transaction hash so the user info is safe.

    Usage:
        1. `wallet = Wallet(ocean.web3, private_key=private_key)`

    """

    _last_tx_count = dict()

    def __init__(
        self,
        web3: Web3,
        private_key: Optional[str] = None,
        encrypted_key: dict = None,
        password: Optional[str] = None,
        address: Optional[str] = None,
    ) -> None:
        """Initialises Wallet object."""
        assert private_key or (
            encrypted_key and password
        ), "private_key or encrypted_key and password is required."

        self._web3 = web3
        self._last_tx_count.clear()

        self._password = password
        self._address = address
        self._key = private_key
        if encrypted_key and not private_key:
            assert self._password
            self._key = self._web3.eth.account.decrypt(encrypted_key, self._password)
            if not isinstance(self._key, str):
                self._key = self._key.hex()

        if self._key:
            address = private_key_to_address(self._key)
            assert self._address is None or self._address == address
            self._address = address
            self._password = None

        assert self.private_key, (
            "something is not right, private key is not available. "
            "please check the arguments are valid."
        )

        self._max_gas_price = os.getenv(ENV_MAX_GAS_PRICE, None)

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def address(self) -> str:
        return self._address

    @property
    def password(self) -> Optional[str]:
        return self._password

    @property
    def private_key(self) -> str:
        return self._key

    @property
    def key(self) -> str:
        return self._key

    @staticmethod
    def reset_tx_count() -> None:
        Wallet._last_tx_count = dict()

    def __get_key(self) -> Optional[str]:
        return self._key

    def validate(self) -> bool:
        account = self._web3.eth.account.from_key(self._key)
        return account.address == self._address

    @staticmethod
    def _get_nonce(web3: Web3, address: str) -> int:
        # We cannot rely on `web3.eth.get_transaction_count` because when sending multiple
        # transactions in a row without wait in between the network may not get the chance to
        # update the transaction count for the account address in time.
        # So we have to manage this internally per account address.
        if address not in Wallet._last_tx_count:
            Wallet._last_tx_count[address] = web3.eth.get_transaction_count(address)
        else:
            Wallet._last_tx_count[address] += 1

        return Wallet._last_tx_count[address]

    def sign_tx(
        self,
        tx: Dict[str, Union[int, str, bytes]],
        fixed_nonce: Optional[int] = None,
        gas_price: Optional[int] = None,
    ) -> HexBytes:
        account = self._web3.eth.account.from_key(self.private_key)
        if fixed_nonce is not None:
            nonce = fixed_nonce
            logger.debug(
                f"Signing transaction using a fixed nonce {fixed_nonce}, tx params are: {tx}"
            )
        else:
            nonce = Wallet._get_nonce(self._web3, account.address)

        if not gas_price:
            gas_price = int(self._web3.eth.gas_price * 1.1)
            gas_price = max(gas_price, MIN_GAS_PRICE)

        if gas_price and self._max_gas_price:
            gas_price = min(gas_price, self._max_gas_price)

        logger.debug(
            f"`Wallet` signing tx: sender address: {account.address} nonce: {nonce}, "
            f"eth.gasPrice: {self._web3.eth.gas_price}"
        )
        tx["gasPrice"] = gas_price
        tx["nonce"] = nonce
        signed_tx = self._web3.eth.account.sign_transaction(tx, self.private_key)
        logger.debug(f"Using gasPrice: {gas_price}")
        logger.debug(f"`Wallet` signed tx is {signed_tx}")
        return signed_tx.rawTransaction

    def sign(self, msg_hash: SignableMessage) -> SignedMessage:
        """Sign a transaction."""
        account = self._web3.eth.account.from_key(self.private_key)
        return account.sign_message(msg_hash)

    def keys_str(self) -> str:
        s = []
        s += [f"address: {self.address}"]
        if self.private_key is not None:
            s += [f"private key: {self.private_key}"]
            s += [f"public key: {private_key_to_public_key(self.private_key)}"]
        s += [""]
        return "\n".join(s)

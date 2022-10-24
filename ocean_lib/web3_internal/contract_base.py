#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
from typing import Any, Optional

from brownie import network
from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from web3 import Web3

from ocean_lib.example_config import NETWORK_IDS
from ocean_lib.web3_internal.contract_utils import get_web3, load_contract
from ocean_lib.web3_internal.transactions import wait_for_transaction_status
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    @enforce_types
    def __init__(self, config_dict: dict, address: Optional[str]) -> None:
        """Initialises Contract Base object."""
        self.name = self.contract_name
        assert (
            self.name
        ), "contract_name property needs to be implemented in subclasses."

        if "CHAIN_ID" not in config_dict:
            w3 = get_web3(config_dict["RPC_URL"])
            # cache it to prevent further calls
            config_dict["CHAIN_ID"] = w3.eth.chain_id

        self.config_dict = config_dict

        self.network = NETWORK_IDS[config_dict["CHAIN_ID"]]
        self.connect_to_network()

        self.contract = load_contract(self.name, address)
        assert not address or (
            self.contract.address.lower() == address.lower()
            and self.address.lower() == address.lower()
        )

    def connect_to_network(self):
        if network.show_active() != self.network:
            if network.is_connected():
                network.disconnect()

            network.connect(self.network)

    def __getattribute__(self, attr):
        method = object.__getattribute__(self, attr)
        if not method:
            raise Exception("Method %s not implemented" % attr)
        if callable(method) and not method.__name__ == "connect_to_network":
            self.connect_to_network()

        return method

    @enforce_types
    def __str__(self) -> str:
        """Returns contract `name @ address.`"""
        return f"{self.contract_name} @ {self.address}"

    @property
    @enforce_types
    def contract_name(self) -> str:
        """Returns the contract name"""
        return self.CONTRACT_NAME

    @property
    @enforce_types
    def address(self) -> str:
        """Return the ethereum address of the solidity contract deployed in current network."""
        return self.contract.address

    @staticmethod
    @enforce_types
    def to_checksum_address(address: str) -> ChecksumAddress:
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.toChecksumAddress(address.lower())

    @enforce_types
    def send_transaction(
        self,
        fn_name: str,
        fn_args: Any,
        from_wallet: Wallet,
        transact: Optional[dict] = None,
    ) -> str:
        """Calls a smart contract function.

        :param fn_name: str the smart contract function name
        :param fn_args: tuple arguments to pass to function above
        :param from_wallet:
        :param transact: dict arguments for the transaction such as from, gas, etc.
        :return: hex str transaction hash
        """
        # only for debugging local ganache
        # w3 = get_web3(self.config_dict["RPC_URL"])

        _transact = {
            "from": ContractBase.to_checksum_address(from_wallet.address),
            "account_key": from_wallet.key,
            # only for debugging local ganache
            # "nonce": w3.eth.getTransactionCount(from_wallet.address)
        }

        if transact:
            _transact.update(transact)

        receipt = getattr(self.contract, fn_name)(*fn_args, _transact)
        receipt.wait(self.config_dict["BLOCK_CONFIRMATIONS"])

        txid = receipt.txid

        return wait_for_transaction_status(
            txid, self.config_dict["TRANSACTION_TIMEOUT"]
        )

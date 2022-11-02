#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
from typing import Any, Optional

from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from web3 import Web3

from ocean_lib.web3_internal.contract_utils import load_contract
from ocean_lib.web3_internal.transactions import wait_for_transaction_status
from ocean_lib.web3_internal.utils import check_network

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

        self.config_dict = config_dict

        self.network = config_dict["NETWORK_NAME"]
        check_network(self.network)

        self.contract = load_contract(self.name, address)
        assert not address or (
            self.contract.address.lower() == address.lower()
            and self.address.lower() == address.lower()
        )

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
        from_wallet,
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
        # from brownie.network import accounts

        _transact = {
            "from": from_wallet,
            # only for debugging local ganache
            # "nonce": nonce
        }

        # only for debugging local ganache
        # import time
        # time.sleep(3)

        if transact:
            _transact.update(transact)

        receipt = getattr(self.contract, fn_name)(*fn_args, _transact)

        txid = receipt.txid

        return wait_for_transaction_status(
            txid, self.config_dict["TRANSACTION_TIMEOUT"]
        )

    def __getattribute__(self, attr):
        try:
            return object.__getattribute__(self, attr)
        except AttributeError:
            return object.__getattribute__(self.contract, attr)

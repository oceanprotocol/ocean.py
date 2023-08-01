#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
from typing import Optional

from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from web3.main import Web3

from ocean_lib.web3_internal.contract_utils import load_contract

logger = logging.getLogger(__name__)


def function_wrapper(contract, web3, contract_functions, func_name):
    if hasattr(contract, func_name):
        return getattr(contract, func_name)

    def wrap(*args, **kwargs):
        args2 = list(args)

        tx_dict = None

        if args and isinstance(args[-1], dict):
            tx_dict = args[-1] if args[-1].get("from") else None
            args2 = list(args[:-1])

        if "tx_dict" in kwargs:
            tx_dict = kwargs["tx_dict"] if kwargs["tx_dict"].get("from") else None
            del kwargs["tx_dict"]

        for arg in args2:
            if hasattr(arg, "address"):
                args2 = list(args2)
                args2[args2.index(arg)] = arg.address

        func = getattr(contract_functions, func_name)
        result = func(*args2, **kwargs)

        if not tx_dict and result.abi["stateMutability"] not in ["view", "pure"]:
            raise Exception("Needs tx_dict with 'from' key.")

        if result.abi["stateMutability"] in ["view", "pure"]:
            return result.call()
        else:
            tx_dict["from"] = (
                tx_dict["from"].address
                if hasattr(tx_dict["from"], "address")
                else tx_dict["from"]
            )
            result = result.transact(tx_dict)

            return web3.eth.wait_for_transaction_receipt(result)

    return wrap


class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    @enforce_types
    def __init__(self, config_dict: dict, address: Optional[str]) -> None:
        """Initialises Contract Base object."""
        assert (
            self.contract_name
        ), "contract_name property needs to be implemented in subclasses."

        self.config_dict = config_dict

        self.contract = load_contract(
            config_dict["web3_instance"], self.contract_name, address
        )
        assert not address or (self.contract.address.lower() == address.lower())

        transferable = [
            x for x in dir(self.contract.functions) if not x.startswith("_")
        ]

        for function in transferable:
            setattr(
                self,
                function,
                function_wrapper(
                    self.contract,
                    config_dict["web3_instance"],
                    self.contract.functions,
                    function,
                ),
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

    @staticmethod
    @enforce_types
    def to_checksum_address(address: str) -> ChecksumAddress:
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.toChecksumAddress(address.lower())

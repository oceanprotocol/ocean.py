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

        self.contract = load_contract(self.contract_name, address)
        assert not address or (self.contract.address.lower() == address.lower())

        transferable = [x for x in dir(self.contract) if not x.startswith("_")]
        for function in transferable:
            setattr(self, function, getattr(self.contract, function))

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

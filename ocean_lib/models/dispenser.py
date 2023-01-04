#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.ocean.util import from_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase


class Dispenser(ContractBase):
    CONTRACT_NAME = "Dispenser"


class DispenserStatus:
    """Status of dispenser smart contract, for a given datatoken"""

    def __init__(self, status_tup):
        """
        :param:status_tup -- returned from Dispenser.sol::status(dt_addr)
        which is (bool active, address owner, bool isMinter,
        uint256 maxTokens, uint256 maxBalance, uint256 balance,
        address allowedSwapper)
        """
        t = status_tup
        self.active: bool = t[0]
        self.owner_address: str = t[1]
        self.is_minter: bool = t[2]
        self.max_tokens: int = t[3]
        self.max_balance: int = t[4]
        self.balance: int = t[5]
        self.allowed_swapper: int = t[6]

    def __str__(self):
        s = (
            f"DispenserStatus: "
            f"  active = {self.active}\n"
            f"  owner_address = {self.owner_address}\n"
            f"  balance (of tokens) = {_strWithWei(self.balance)}\n"
            f"  is_minter (can mint more tokens?) = {self.is_minter}\n"
            f"  max_tokens (to dispense) = {_strWithWei(self.max_tokens)}\n"
            f"  max_balance (of requester) = {_strWithWei(self.max_balance)}\n"
        )
        if self.allowed_swapper.lower() == ZERO_ADDRESS.lower():
            s += "  allowed_swapper = anyone can request\n"
        else:
            s += f"  allowed_swapper = {self.allowed_swapper}\n"
        return s


@enforce_types
def _strWithWei(x_wei: int) -> str:
    return f"{from_wei(x_wei)} ({x_wei} wei)"

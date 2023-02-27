#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional, Union

from enforce_typing import enforce_types

from ocean_lib.ocean.util import from_wei, get_address_of_type
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

"""
def activate(dt_addr: str, max_tokens: int, max_balance: int) -> None:
    activate dispenser after deactivation
    :param dt_addr: datatoken address of ERC20
    :param max_tokens: maximum amount of tokens
    :param max_balance: maximum token balance
    :return: None

def balance() -> int:
    get dispenser balance
    :return: balance in int

def deactivate(dt_addr: str) -> None:
    deactivate dispenser
    :param dt_addr: datatoken address of ERC20
    :return: None

def dispense(dt_addr: str, amount: int, destination: str) -> None:
    dispense an amount of tokens to a given destination address,
    requires tx_dict with a sender that can dispense
    :param dt_addr: address of the ERC20 token
    :param amount: amount to dispense
    :param destination: address of the account to receive dispensed tokens
    :return: None

def getId() -> int:
    get dispenser id
    :return: dispenser id

def ownerWithdraw(dt_addr: str) -> None:
    withdraw datatokens from dispenser,
    requires tx_dict with a sender that can dispense
    :param dt_addr: address of the ERC20 token. If missing, will withdraw all.
    :return: None

def setAllowedSwapper(dt_addr: str, new_swapper_addr: str) -> None:
    set allowed swapper to a new address
    :param dt_addr: address of the ERC20 token
    :param new_swapper_addr: address of the account to be set as swapper
    :return: None


The following functions are wrapped with ocean.py helpers, but you can use the raw form if needed:
status -> you can use the datatoken.dispenser_status() function as a better shorthand
create -> you can use the datatoken.create_dispenser() function as a better shorthand
datatokensList -> a list of datatokens served by this dispenser, but we recommend retrieving each dispenser from its datatoken object
"""


class Dispenser(ContractBase):
    CONTRACT_NAME = "Dispenser"


class DispenserArguments:
    def __init__(
        self,
        max_tokens: Optional[Union[int, str]] = MAX_UINT256,
        max_balance: Optional[Union[int, str]] = MAX_UINT256,
        with_mint: Optional[bool] = True,
        allowed_swapper: Optional[str] = ZERO_ADDRESS,
    ):
        self.max_tokens = max_tokens
        self.max_balance = max_balance
        self.with_mint = with_mint
        self.allowed_swapper = ContractBase.to_checksum_address(allowed_swapper)

    def to_tuple(self, config_dict):
        dispenser_address = get_address_of_type(config_dict, "Dispenser")
        return (
            ContractBase.to_checksum_address(dispenser_address),
            self.max_tokens,
            self.max_balance,
            self.with_mint,
            self.allowed_swapper,
        )


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

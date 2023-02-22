#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken_base import DatatokenBase, TokenFeeInfo
from ocean_lib.ocean.util import from_wei, get_address_of_type, get_from_address, to_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address
logger = logging.getLogger("ocean")

"""
def addMinter(address: str) -> None:
    add a minter for the datatoken
    :param address: address of interest
    :return: None

def addPaymentManager(address: str) -> None:
    add a payment manager for the datatoken
    :param address: address of interest
    :return: None

def allowance(owner_addr: str, spender_addr: str) -> int:
    get token allowance for spender from owner
    :param owner_addr: address of owner
    :param spender_addr: address of owner
    :return: int allowance

def approve(address: str, amount: int) -> None:
    approve tokens for a specific address in the given amount
    :param address: address of interest
    :param amount: amount in int
    :return: None

def authERC20(index: int) -> tuple:
    get user permissions on ERC20 for specific index
    :param index: index of interest
    :return: tuple of tuples of boolean values for minter role, payment manager role

def balance() -> int:
    get token balance
    :return: int

def balanceOf(address: str) -> int:
    get token balance for specific address
    :param address: address of interest
    :return: int

def burn(amount: int) -> None:
    burn a specific amount of tokens
    :param amount: amount in int
    :return: None

def burnFrom(address: str, amount: int) -> None:
    burn a specific amount of tokens from an account
    :param address: address of the burner account
    :param amount: amount in int
    :return: None

def cap() -> int:
    get token cap
    :return: int

def cleanPermissions() -> None:
    reset all permissions on token,
    must include the tx_dict with the publisher as transaction sender
    :return: None

def decimals() -> int:
    get token decimals
    :return: int

def decreaseAllowance(address: str, amount: int) -> None:
    decrease the allowance for an address by a specific amount
    :param address: address of the account
    :param amount: amount to subtract in int
    :return: None

def getERC721Address() -> str:
    get address of ERC721 token
    :return: str

def getId() -> int:
    get token Id
    :return: id

def getPaymentCollector() -> str:
    get payment collector address
    :return: address of payment collector

def getPermissions(user: str) -> tuple:
    get user permissions
    :param user: account address of interest
    :return: tuple of boolean values for minter role, payment manager role

def increaseAllowance(address: str, amount: int) -> None:
    increase the allowance for an address by a specific amount
    :param address: address of the account
    :param amount: amount to add in int
    :return: None

def isERC20Deployer(address: str) -> bool:
    returns whether an address has ERC20 Deployer role
    :param address: address of interest
    :return: bool

def isMinter(address: str) -> bool:
    returns whether an address has minter role
    :param address: address of interest
    :return: bool

def mint(address: str, amount: int) -> None:
    mints am amount of tokens for the given address,
    requires tx_dict with a datatoken minter as the sender
    returns whether an address has minter role
    :param address: address of interest
    :param amount: amount to mint
    :return: None

def name() -> str:
    :return: name of token

def removeMinter(address: str) -> None:
    remove minter role for the datatoken
    :param address: address of interest
    :return: None

def removePaymentManager(address: str) -> None:
    remove payment manager role for the datatoken
    :param address: address of interest
    :return: None

def setData(key: bytes, value: bytes) -> None:
    set a key, value pair on the token
    :param key:
    :param bytes:
    :return: None

def setPaymentCollector(address: str) -> None:
    set payment collector address
    :param address: address of payment collector
    :return: None

def setPublishingMarketFee(address: str, token: str, amount: int) -> None:
    set publishing market fee
    :param address: address of the intended receiver
    :param token: address of the token to receive fees in
    :param amount: amount of intended fee
    :return: None

def symbol() -> str:
    :return: symbol of token

def totalSupply() -> int:
    :return: total supply of token

def transfer(to: str, amount: int) -> None:
    transfer an amount of tokens from transaction sender to address,
    requires tx_dict with a datatoken minter as the sender
    :param to: address of destination account
    :param amount: amount to transfer
    :return: None

def transferFrom(from: str, to: str, amount: int) -> None:
    transfer an amount of tokens from one address to another,
    requires tx_dict with a datatoken minter as the sender
    :param from: address of current owner account
    :param to: address of destination account
    :param amount: amount to transfer
    :return: None

def withdrawETH() -> None:
    withdraws all available ETH into the owner account
    :return: None


The following functions are wrapped with ocean.py helpers, but you can use the raw form if needed:
createDispenser
createFixedRate
getDispensers
getFixedRates
getPublishingMarketFee
reuseOrder
startOrder
"""


class Datatoken1(DatatokenBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    # ===========================================================================
    # consume

    def dispense_and_order(
        self,
        provider_fees: dict,
        tx_dict: dict,
        consumer: Optional[str] = None,
        service_index: int = 1,
        consume_market_fees=None,
    ) -> str:
        if not consumer:
            consumer = get_from_address(tx_dict)

        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

        buyer_addr = get_from_address(tx_dict)

        bal = from_wei(self.balanceOf(buyer_addr))
        if bal < 1.0:
            dispenser_addr = get_address_of_type(self.config_dict, "Dispenser")
            from ocean_lib.models.dispenser import Dispenser  # isort: skip

            dispenser = Dispenser(self.config_dict, dispenser_addr)

            # catch key failure modes
            st = dispenser.status(self.address)
            active, allowedSwapper = st[0], st[6]
            if not active:
                raise ValueError("No active dispenser for datatoken")
            if allowedSwapper not in [ZERO_ADDRESS, buyer_addr]:
                raise ValueError(f"Not allowed. allowedSwapper={allowedSwapper}")

            # Try to dispense. If other issues, they'll pop out
            dispenser.dispense(self.address, "1 ether", buyer_addr, tx_dict)

        return self.start_order(
            consumer=ContractBase.to_checksum_address(consumer),
            service_index=service_index,
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            tx_dict=tx_dict,
        )

    @enforce_types
    def buy_DT_and_order(
        self,
        provider_fees: dict,
        exchange: Any,
        tx_dict: dict,
        consumer: Optional[str] = None,
        service_index: int = 1,
        consume_market_fees=None,
    ) -> str:
        if not consumer:
            consumer = get_from_address(tx_dict)

        fre_address = get_address_of_type(self.config_dict, "FixedPrice")

        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

        if not isinstance(exchange, OneExchange):
            exchange = OneExchange(fre_address, exchange)

        exchange.buy_DT(
            datatoken_amt=to_wei(1),
            consume_market_fee_addr=consume_market_fees.address,
            consume_market_fee=consume_market_fees.amount,
            tx_dict=tx_dict,
        )

        return self.start_order(
            consumer=ContractBase.to_checksum_address(consumer),
            service_index=service_index,
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            tx_dict=tx_dict,
        )

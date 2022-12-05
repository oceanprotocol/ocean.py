#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum

from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.web3_internal.contract_base import ContractBase


class FixedRateExchangeDetails(IntEnum):
    EXCHANGE_OWNER = 0
    DATATOKEN = 1
    DT_DECIMALS = 2
    BASE_TOKEN = 3
    BT_DECIMALS = 4
    FIXED_RATE = 5
    ACTIVE = 6
    DT_SUPPLY = 7
    BT_SUPPLY = 8
    DT_BALANCE = 9
    BT_BALANCE = 10
    WITH_MINT = 11


class FixedRateExchangeFeesInfo(IntEnum):
    MARKET_FEE = 0
    MARKET_FEE_COLLECTOR = 1
    OPC_FEE = 2
    MARKET_FEE_AVAILABLE = 3
    OCEAN_FEE_AVAILABLE = 4


class FixedExchangeBaseInOutData(IntEnum):
    BASE_TOKEN_AMOUNT = 0
    BASE_TOKEN_AMOUNT_BEFORE_FEE = 1
    OCEAN_FEE_AMOUNT = 2
    MARKET_FEE_AMOUNT = 3


class FixedRateExchange(ContractBase):
    CONTRACT_NAME = "FixedRateExchange"


class MockExchange(ContractBase):
    CONTRACT_NAME = "MockExchange"


class FixedRateExchangeStatus:
    def __init__(self, status_tup):
        """
        :param:status_tup -- returned from Dispenser.sol::status(dt_addr)
        which is (bool active, address owner, bool isMinter,
        uint256 maxTokens, uint256 maxBalance, uint256 balance,
        address allowedSwapper)
        """
        t = status_tup
        self.exchangeOwner: str = t[0]
        self.datatoken: str = t[1]
        self.dtDecimals: int = t[2]
        self.baseToken: str = t[3]
        self.btDecimals: int = t[4]
        self.fixedRate: int = t[5]
        self.active: bool = t[6]
        self.dtSupply: int = t[7]
        self.btSupply: int = t[8]
        self.dtBalance: int = t[9]
        self.btBalance: int = t[10]
        self.withMint: bool = t[11]

    def __str__(self):
        s = (
            f"FixedRateExchangeStatus: \n"
            f"  datatoken = {self.datatoken}\n"
            f"  baseToken = {self.baseToken}\n"
            f"  price in baseToken (fixedRate) = {_strWithWei(self.fixedRate)}\n"
            f"  active = {self.active}\n"
            f"  dtSupply = {_strWithWei(self.dtSupply)}\n"
            f"  btSupply = {_strWithWei(self.btSupply)}\n"
            f"  dtBalance = {_strWithWei(self.dtBalance)}\n"
            f"  btBalance = {_strWithWei(self.btBalance)}\n"
            f"  withMint = {self.withMint}\n"
            f"  dtDecimals = {self.dtDecimals}\n"
            f"  btDecimals = {self.btDecimals}\n"
            f"  exchangeOwner = {self.exchangeOwner}\n"
        )
        return s


@enforce_types
def _strWithWei(x_wei: int) -> str:
    return f"{Web3.fromWei(x_wei, 'ether')} ({x_wei} wei)"

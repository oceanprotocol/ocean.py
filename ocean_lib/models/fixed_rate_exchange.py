#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum

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

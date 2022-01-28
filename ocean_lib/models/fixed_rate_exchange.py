#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List

from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


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


@enforce_types
class FixedRateExchange(ContractBase):
    CONTRACT_NAME = "FixedRateExchange"
    EVENT_EXCHANGE_CREATED = "ExchangeCreated"
    EVENT_EXCHANGE_RATE_CHANGED = "ExchangeRateChanged"
    EVENT_EXCHANGE_ACTIVATED = "ExchangeActivated"
    EVENT_EXCHANGE_DEACTIVATED = "ExchangeDeactivated"
    EVENT_SWAPPED = "Swapped"
    EVENT_TOKEN_COLLECTED = "TokenCollected"
    EVENT_OCEAN_FEE_COLLECTED = "OceanFeeCollected"
    EVENT_MARKET_FEE_COLLECTED = "MarketFeeCollected"

    @property
    def event_ExchangeCreated(self):
        return self.events.ExchangeCreated()

    @property
    def event_ExchangeRateChanged(self):
        return self.events.ExchangeRateChanged()

    @property
    def event_ExchangeActivated(self):
        return self.events.ExchangeActivated()

    @property
    def event_ExchangeDeactivated(self):
        return self.events.ExchangeDeactivated()

    @property
    def event_Swapped(self):
        return self.events.Swapped()

    @property
    def event_TokenCollected(self):
        return self.events.TokenCollected()

    @property
    def event_OceanFeeCollected(self):
        return self.events.OceanFeeCollected()

    @property
    def event_MarketFeeCollected(self):
        return self.events.MarketFeeCollected()

    def get_opc_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPCFee(base_token)

    def generate_exchange_id(
        self, base_token: str, datatoken: str, exchange_owner: str
    ) -> bytes:
        return self.contract.caller.generateExchangeId(
            base_token, datatoken, exchange_owner
        )

    def calc_base_in_given_out_dt(
        self, exchange_id: bytes, datatoken_amount: int
    ) -> tuple:
        return self.contract.caller.calcBaseInGivenOutDT(exchange_id, datatoken_amount)

    def calc_base_out_given_in_dt(
        self, exchange_id: bytes, datatoken_amount: int
    ) -> tuple:
        return self.contract.caller.calcBaseOutGivenInDT(exchange_id, datatoken_amount)

    def buy_dt(
        self,
        exchange_id: bytes,
        datatoken_amount: int,
        max_base_token_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "buyDT", (exchange_id, datatoken_amount, max_base_token_amount), from_wallet
        )

    def sell_dt(
        self,
        exchange_id: bytes,
        datatoken_amount: int,
        min_base_token_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "sellDT",
            (exchange_id, datatoken_amount, min_base_token_amount),
            from_wallet,
        )

    def collect_bt(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("collectBT", (exchange_id,), from_wallet)

    def collect_dt(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("collectDT", (exchange_id,), from_wallet)

    def collect_market_fee(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("collectMarketFee", (exchange_id,), from_wallet)

    def collect_ocean_fee(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("collectOceanFee", (exchange_id,), from_wallet)

    def update_market_fee_collector(
        self, exchange_id: bytes, new_market_fee_collector: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "updateMarketFeeCollector",
            (exchange_id, new_market_fee_collector),
            from_wallet,
        )

    def update_market_fee(
        self, exchange_id: bytes, new_market_fee: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "updateMarketFee", (exchange_id, new_market_fee), from_wallet
        )

    def get_number_of_exchanges(self) -> int:
        return self.contract.caller.getNumberOfExchanges()

    def get_allowed_swapper(self, exchange_id: bytes) -> str:
        return self.contract.caller.getAllowedSwapper(exchange_id)

    def set_rate(self, exchange_id: bytes, new_rate: int, from_wallet: Wallet) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

    def set_allowed_swapper(
        self, exchange_id: bytes, new_allowed_swapper: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setAllowedSwapper", (exchange_id, new_allowed_swapper), from_wallet
        )

    def toggle_exchange_state(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    def get_rate(self, exchange_id: bytes) -> int:
        return self.contract.caller.getRate(exchange_id)

    def get_dt_supply(self, exchange_id: bytes) -> int:
        return self.contract.caller.getDTSupply(exchange_id)

    def get_bt_supply(self, exchange_id: bytes) -> int:
        return self.contract.caller.getBTSupply(exchange_id)

    def get_exchange(self, exchange_id: bytes) -> tuple:
        return self.contract.caller.getExchange(exchange_id)

    def get_fees_info(self, exchange_id: bytes) -> tuple:
        return self.contract.caller.getFeesInfo(exchange_id)

    def get_exchanges(self) -> List[bytes]:
        return self.contract.caller.getExchanges()

    def is_active(self, exchange_id: bytes) -> bool:
        return self.contract.caller.isActive(exchange_id)


@enforce_types
class MockExchange(ContractBase):
    CONTRACT_NAME = "MockExchange"

    def deposit_with_permit(
        self,
        token: str,
        amount: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "depositWithPermit", (token, amount, deadline, v, r, s), from_wallet
        )

    def deposit(self, token: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("deposit", (token, amount), from_wallet)

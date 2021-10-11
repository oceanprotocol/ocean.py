#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class FixedRateExchangeV4(ContractBase):
    CONTRACT_NAME = "FixedRateExchange"
    EVENT_EXCHANGE_CREATED = "ExchangeCreated"
    EVENT_EXCHANGE_RATE_CREATED = "ExchangeRateChanged"
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

    def get_opf_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPFFee(base_token)

    def generate_exchange_id(
        self, base_token: str, data_token: str, exchange_owner: str
    ) -> bytes:
        return self.contract.caller.generateExchangeId(
            base_token, data_token, exchange_owner
        )

    def calc_base_in_given_out_dt(
        self, exchange_id: bytes, data_token_amount: int
    ) -> tuple:
        return self.contract.caller.calcBaseInGivenOutDT(exchange_id, data_token_amount)

    def calc_base_out_given_in_dt(
        self, exchange_id: bytes, data_token_amount: int
    ) -> tuple:
        return self.contract.caller.calcBaseOutGivenInDT(exchange_id, data_token_amount)

    def buy_dt(
        self, exchange_id: bytes, data_token_amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "buyDT", (exchange_id, data_token_amount), from_wallet
        )

    def sell_dt(
        self, exchange_id: bytes, data_token_amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "sellDT", (exchange_id, data_token_amount), from_wallet
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

    def get_number_of_exchanges(self) -> int:
        return self.contract.caller.getNumberOfExchanges()

    def set_rate(self, exchange_id: bytes, new_rate: int, from_wallet: Wallet) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

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

    def get_exchanges(self) -> bytes:
        return self.contract.caller.getExchanges()

    def is_active(self, exchange_id: bytes) -> bool:
        return self.contract.caller.isActive(exchange_id)

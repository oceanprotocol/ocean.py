#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Union

from enforce_typing import enforce_types

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
    EVENT_EXCHANGE_CREATED = "ExchangeCreated"
    EVENT_EXCHANGE_RATE_CHANGED = "ExchangeRateChanged"
    EVENT_EXCHANGE_ACTIVATED = "ExchangeActivated"
    EVENT_EXCHANGE_DEACTIVATED = "ExchangeDeactivated"
    EVENT_SWAPPED = "Swapped"
    EVENT_TOKEN_COLLECTED = "TokenCollected"
    EVENT_OCEAN_FEE_COLLECTED = "OceanFeeCollected"
    EVENT_MARKET_FEE_COLLECTED = "MarketFeeCollected"
    EVENT_CONSUME_MARKET_FEE = "ConsumeMarketFee"
    EVENT_LOG_SWAP_FEES = "SWAP_FEES"
    EVENT_PUBLISH_MARKET_FEE_CHANGED = "PublishMarketFeeChanged"

    @enforce_types
    def router(self) -> str:
        return self.contract.router()

    @enforce_types
    def get_opc_fee(self, base_token: str) -> int:
        return self.contract.getOPCFee(base_token)

    @enforce_types
    def generate_exchange_id(self, base_token: str, datatoken: str) -> str:
        return self.contract.generateExchangeId(
            ContractBase.to_checksum_address(base_token),
            ContractBase.to_checksum_address(datatoken),
        )

    def get_base_token_out_price(self, exchange_id: str, dt_amount: int) -> int:
        return self.contract.getBaseTokenOutPrice(exchange_id, dt_amount)

    def calc_base_in_given_out_dt(
        self,
        exchange_id: str,
        datatoken_amount: int,
        consume_market_swap_fee_amount: int,
    ) -> tuple:
        return self.contract.calcBaseInGivenOutDT(
            exchange_id, datatoken_amount, consume_market_swap_fee_amount
        )

    def calc_base_out_given_in_dt(
        self,
        exchange_id: str,
        datatoken_amount: int,
        consume_market_swap_fee_amount: int,
    ) -> tuple:
        return self.contract.calcBaseOutGivenInDT(
            exchange_id, datatoken_amount, consume_market_swap_fee_amount
        )

    def buy_dt(
        self,
        exchange_id: str,
        datatoken_amount: int,
        max_base_token_amount: int,
        consume_market_swap_fee_address: str,
        consume_market_swap_fee_amount: int,
        from_wallet,
    ) -> str:
        return self.send_transaction(
            "buyDT",
            (
                exchange_id,
                datatoken_amount,
                max_base_token_amount,
                ContractBase.to_checksum_address(consume_market_swap_fee_address),
                consume_market_swap_fee_amount,
            ),
            from_wallet,
        )

    def sell_dt(
        self,
        exchange_id: str,
        datatoken_amount: int,
        min_base_token_amount: int,
        consume_market_swap_fee_address: str,
        consume_market_swap_fee_amount: int,
        from_wallet,
    ) -> str:
        return self.send_transaction(
            "sellDT",
            (
                exchange_id,
                datatoken_amount,
                min_base_token_amount,
                ContractBase.to_checksum_address(consume_market_swap_fee_address),
                consume_market_swap_fee_amount,
            ),
            from_wallet,
        )

    def collect_bt(self, exchange_id: str, amount: int, from_wallet) -> str:
        return self.send_transaction(
            "collectBT",
            (
                exchange_id,
                amount,
            ),
            from_wallet,
        )

    def collect_dt(self, exchange_id: str, amount: int, from_wallet) -> str:
        return self.send_transaction(
            "collectDT",
            (
                exchange_id,
                amount,
            ),
            from_wallet,
        )

    def collect_market_fee(self, exchange_id: str, from_wallet) -> str:
        return self.send_transaction("collectMarketFee", (exchange_id,), from_wallet)

    def collect_ocean_fee(self, exchange_id: str, from_wallet) -> str:
        return self.send_transaction("collectOceanFee", (exchange_id,), from_wallet)

    def update_market_fee_collector(
        self,
        exchange_id: str,
        publish_market_swap_fee_collector: str,
        from_wallet,
    ) -> str:
        return self.send_transaction(
            "updateMarketFeeCollector",
            (
                exchange_id,
                ContractBase.to_checksum_address(publish_market_swap_fee_collector),
            ),
            from_wallet,
        )

    def update_market_fee(
        self,
        exchange_id: str,
        publish_market_swap_fee_amount: int,
        from_wallet,
    ) -> str:
        return self.send_transaction(
            "updateMarketFee",
            (exchange_id, publish_market_swap_fee_amount),
            from_wallet,
        )

    def get_market_fee(
        self,
        exchange_id: str,
    ) -> int:
        return self.contract.getMarketFee(exchange_id)

    @enforce_types
    def get_number_of_exchanges(self) -> int:
        return self.contract.getNumberOfExchanges()

    def get_allowed_swapper(self, exchange_id: str) -> str:
        return self.contract.getAllowedSwapper(exchange_id)

    def set_rate(self, exchange_id: str, new_rate: int, from_wallet) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

    def set_allowed_swapper(
        self, exchange_id: str, new_allowed_swapper: str, from_wallet
    ) -> str:
        return self.send_transaction(
            "setAllowedSwapper",
            (exchange_id, ContractBase.to_checksum_address(new_allowed_swapper)),
            from_wallet,
        )

    def toggle_exchange_state(self, exchange_id: str, from_wallet) -> str:
        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    def get_rate(self, exchange_id: str) -> int:
        return self.contract.getRate(exchange_id)

    def get_dt_supply(self, exchange_id: str) -> int:
        return self.contract.getDTSupply(exchange_id)

    def get_bt_supply(self, exchange_id: str) -> int:
        return self.contract.getBTSupply(exchange_id)

    def get_exchange(self, exchange_id: str) -> tuple:
        return self.contract.getExchange(exchange_id)

    def get_fees_info(self, exchange_id: str) -> tuple:
        return self.contract.getFeesInfo(exchange_id)

    @enforce_types
    def get_exchanges(self) -> List[str]:
        return self.contract.getExchanges()

    def is_active(self, exchange_id: str) -> bool:
        return self.contract.isActive(exchange_id)


class MockExchange(ContractBase):
    CONTRACT_NAME = "MockExchange"

    @enforce_types
    def deposit_with_permit(
        self,
        token: str,
        amount: int,
        deadline: int,
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        from_wallet,
    ):
        return self.send_transaction(
            "depositWithPermit",
            (ContractBase.to_checksum_address(token), amount, deadline, v, r, s),
            from_wallet,
        )

    @enforce_types
    def deposit(self, token: str, amount: int, from_wallet) -> str:
        return self.send_transaction(
            "deposit", (ContractBase.to_checksum_address(token), amount), from_wallet
        )

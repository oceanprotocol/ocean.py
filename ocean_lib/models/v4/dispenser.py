#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class DispenserV4(ContractBase):
    CONTRACT_NAME = "Dispenser"
    EVENT_EXCHANGE_CREATED = "ExchangeCreated"
    EVENT_EXCHANGE_ACTIVATED = "ExchangeActivated"
    EVENT_EXCHANGE_DEACTIVATED = "ExchangeDeactivated"
    EVENT_TOKEN_DISPENSED = "TokenDispensed"
    EVENT_TOKEN_DEVOLUTION = "TokenDevolution"
    EVENT_TOKEN_COLLECTED = "TokenCollected"

    @property
    def event_ExchangeCreated(self):
        return self.events.ExchangeCreated()

    @property
    def event_ExchangeActivated(self):
        return self.events.ExchangeActivated()

    @property
    def event_ExchangeDeactivated(self):
        return self.events.ExchangeDeactivated()

    @property
    def event_TokenDispensed(self):
        return self.events.TokenDispensed()

    @property
    def event_TokenDevolution(self):
        return self.events.TokenDevolution()

    @property
    def event_TokenCollected(self):
        return self.events.TokenCollected()

    def generate_exchange_id(self, data_token: str, exchange_owner: str) -> bytes:
        return self.contract.caller.generateExchangeId(data_token, exchange_owner)

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

    def collect_dt(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("collectDT", (exchange_id,), from_wallet)

    def get_number_of_exchanges(self) -> int:
        return self.contract.caller.getNumberOfExchanges()

    def toggle_exchange_state(self, exchange_id: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    def get_rate(self, exchange_id: bytes) -> int:
        return self.contract.caller.getRate(exchange_id)

    def get_dt_supply(self, exchange_id: bytes) -> int:
        return self.contract.caller.getDTSupply(exchange_id)

    def get_exchange(self, exchange_id: bytes) -> tuple:
        return self.contract.caller.getExchange(exchange_id)

    def get_exchanges(self) -> List[bytes]:
        return self.contract.caller.getExchanges()

    def is_active(self, exchange_id: bytes) -> bool:
        return self.contract.caller.isActive(exchange_id)

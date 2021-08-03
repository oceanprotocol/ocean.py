#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet

FixedExchangeData = namedtuple(
    "FixedExchangeData",
    ("exchangeOwner", "dataToken", "baseToken", "fixedRate", "active", "supply"),
)


@enforce_types
class FixedRateExchange(ContractBase):

    """

    Note: all operations accept and return integer values in base 18 format.
    Its up to the caller to convert to/from base 18 as necessary.

    """

    CONTRACT_NAME = "FixedRateExchange"

    def buy_data_token(
        self, exchange_id: str, data_token_amount: int, from_wallet: Wallet
    ) -> str:
        return self.swap(exchange_id, data_token_amount, from_wallet)

    def get_base_token_quote(self, exchange_id: str, data_token_amount: int) -> int:
        rate = self.getRate(exchange_id)
        return int(data_token_amount * rate / to_base_18(1.0))

    #########################
    # Transaction methods
    def create(
        self, base_token: str, data_token: str, exchange_rate: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "create", (base_token, data_token, exchange_rate), from_wallet
        )

    def swap(
        self, exchange_id: str, data_token_amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "swap", (exchange_id, data_token_amount), from_wallet
        )

    def setRate(self, exchange_id: str, new_rate: int, from_wallet: Wallet) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

    def activate(self, exchange_id: str, from_wallet: Wallet) -> Optional[str]:
        if self.isActive(exchange_id):
            return None

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    def deactivate(self, exchange_id: str, from_wallet: Wallet) -> Optional[str]:
        if not self.isActive(exchange_id):
            return None

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    #########################
    # Helper methods
    def generateExchangeId(
        self, base_token: str, data_token: str, exchange_owner: str
    ) -> str:
        return self.contract.caller.generateExchangeId(
            base_token, data_token, exchange_owner
        )

    #########################
    # View/Read-only methods
    def getNumberOfExchanges(self) -> int:
        return self.contract.caller.getNumberOfExchanges()

    def getRate(self, exchange_id: str) -> int:
        return self.contract.caller.getRate(exchange_id)

    def getExchange(self, exchange_id: str) -> Optional[FixedExchangeData]:
        values = self.contract.caller.getExchange(exchange_id)
        if values and len(values) == 6:
            return FixedExchangeData(*values)
        return None

    def getExchanges(self) -> list:
        return self.contract.caller.getExchanges()

    def isActive(self, exchange_id: str) -> bool:
        return self.contract.caller.isActive(exchange_id)

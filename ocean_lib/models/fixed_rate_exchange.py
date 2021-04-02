#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple
from typing import Optional

from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet

FixedExchangeData = namedtuple(
    "FixedExchangeData",
    ("exchangeOwner", "dataToken", "baseToken", "fixedRate", "active", "supply"),
)


@enforce_types_shim
class FixedRateExchange(ContractBase):

    """

    Note: all operations accept and return integer values in base 18 format.
    Its up to the caller to convert to/from base 18 as necessary.

    """

    CONTRACT_NAME = "FixedRateExchange"

    def buy_data_token(
        self, exchange_id: str, data_token_amount: int, from_wallet: Wallet
    ):
        return self.swap(exchange_id, data_token_amount, from_wallet)

    def get_base_token_quote(self, exchange_id: str, data_token_amount: int):
        rate = self.getRate(exchange_id)
        return int(data_token_amount * rate / to_base_18(1.0))

    #########################
    # Transaction methods
    def create(
        self, base_token: str, data_token: str, exchange_rate: int, from_wallet: Wallet
    ):
        return self.send_transaction(
            "create", (base_token, data_token, exchange_rate), from_wallet
        )

    def swap(self, exchange_id: str, data_token_amount: int, from_wallet: Wallet):
        return self.send_transaction(
            "swap", (exchange_id, data_token_amount), from_wallet
        )

    def setRate(self, exchange_id: str, new_rate: int, from_wallet: Wallet) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

    def activate(self, exchange_id: str, from_wallet: Wallet) -> Optional[str]:
        if self.isActive(exchange_id):
            return

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    def deactivate(self, exchange_id: str, from_wallet: Wallet) -> Optional[str]:
        if not self.isActive(exchange_id):
            return

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    #########################
    # Helper methods
    def generateExchangeId(
        self, base_token: str, data_token: str, exchange_owner: str
    ) -> str:
        return self.contract_concise.generateExchangeId(
            base_token, data_token, exchange_owner
        )

    #########################
    # View/Read-only methods
    def getNumberOfExchanges(self) -> int:
        return self.contract_concise.getNumberOfExchanges()

    def getRate(self, exchange_id: str) -> int:
        return self.contract_concise.getRate(exchange_id)

    def getExchange(self, exchange_id: str):
        values = self.contract_concise.getExchange(exchange_id)
        if values and len(values) == 6:
            return FixedExchangeData(*values)
        return None

    def getExchanges(self) -> list:
        return self.contract_concise.getExchanges()

    def isActive(self, exchange_id: str) -> bool:
        return self.contract_concise.isActive(exchange_id)

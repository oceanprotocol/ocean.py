#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple
from typing import Optional, Union

from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet

FixedExchangeData = namedtuple(
    "FixedExchangeData",
    ("exchangeOwner", "dataToken", "baseToken", "fixedRate", "active", "supply"),
)


class FixedRateExchange(ContractBase):

    """

    Note: all operations accept and return integer values, denoted in wei
    Its up to the caller to convert to/from wei as necessary.

    """

    CONTRACT_NAME = "FixedRateExchange"

    @enforce_types
    def buy_data_token(
        self,
        exchange_id: Union[str, bytes],
        data_token_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.swap(exchange_id, data_token_amount, from_wallet)

    @enforce_types
    def get_base_token_quote(
        self, exchange_id: Union[str, bytes], data_token_amount: int
    ) -> int:
        rate = self.getRate(exchange_id)
        return int(data_token_amount * rate / to_wei(1))

    #########################
    # Transaction methods
    @enforce_types
    def create(
        self, base_token: str, data_token: str, exchange_rate: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "create", (base_token, data_token, exchange_rate), from_wallet
        )

    @enforce_types
    def swap(
        self,
        exchange_id: Union[str, bytes],
        data_token_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "swap", (exchange_id, data_token_amount), from_wallet
        )

    @enforce_types
    def setRate(
        self, exchange_id: Union[str, bytes], new_rate: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction("setRate", (exchange_id, new_rate), from_wallet)

    @enforce_types
    def activate(
        self, exchange_id: Union[str, bytes], from_wallet: Wallet
    ) -> Optional[str]:
        if self.isActive(exchange_id):
            return None

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    @enforce_types
    def deactivate(
        self, exchange_id: Union[str, bytes], from_wallet: Wallet
    ) -> Optional[str]:
        if not self.isActive(exchange_id):
            return None

        return self.send_transaction("toggleExchangeState", (exchange_id,), from_wallet)

    #########################
    # Helper methods
    @enforce_types
    def generateExchangeId(
        self, base_token: str, data_token: str, exchange_owner: str
    ) -> str:
        return self.contract.caller.generateExchangeId(
            base_token, data_token, exchange_owner
        )

    #########################
    # View/Read-only methods
    @enforce_types
    def getNumberOfExchanges(self) -> int:
        return self.contract.caller.getNumberOfExchanges()

    @enforce_types
    def getRate(self, exchange_id: Union[str, bytes]) -> int:
        return self.contract.caller.getRate(exchange_id)

    @enforce_types
    def getExchange(
        self, exchange_id: Union[str, bytes]
    ) -> Optional[FixedExchangeData]:
        values = self.contract.caller.getExchange(exchange_id)
        if values and len(values) == 6:
            return FixedExchangeData(*values)
        return None

    @enforce_types
    def getExchanges(self) -> list:
        return self.contract.caller.getExchanges()

    @enforce_types
    def isActive(self, exchange_id: Union[str, bytes]) -> bool:
        return self.contract.caller.isActive(exchange_id)

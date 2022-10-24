#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.contract_base import ContractBase


class Dispenser(ContractBase):
    CONTRACT_NAME = "Dispenser"

    EVENT_DISPENSER_CREATED = "DispenserCreated"
    EVENT_DISPENSER_ACTIVATED = "DispenserActivated"
    EVENT_DISPENSER_DEACTIVATED = "DispenserDeactivated"
    EVENT_ALLOWED_SWAPPER_CHANGED = "DispenserAllowedSwapperChanged"
    EVENT_TOKENS_DISPENSED = "TokensDispensed"
    EVENT_OWNER_WITHDRAWED = "OwnerWithdrawed"

    @enforce_types
    def status(self, datatoken: str) -> tuple:
        return self.contract.status(datatoken)

    @enforce_types
    def activate(
        self, datatoken: str, max_tokens: int, max_balance: int, from_wallet
    ) -> str:
        return self.send_transaction(
            "activate",
            (ContractBase.to_checksum_address(datatoken), max_tokens, max_balance),
            from_wallet,
        )

    def deactivate(self, datatoken: str, from_wallet) -> str:
        return self.send_transaction(
            "deactivate", (ContractBase.to_checksum_address(datatoken),), from_wallet
        )

    def set_allowed_swapper(
        self, datatoken: str, new_allowed_swapper: str, from_wallet
    ) -> str:
        return self.send_transaction(
            "setAllowedSwapper",
            (
                ContractBase.to_checksum_address(datatoken),
                ContractBase.to_checksum_address(new_allowed_swapper),
            ),
            from_wallet,
        )

    @enforce_types
    def dispense(
        self, datatoken: str, amount: int, destination: str, from_wallet
    ) -> str:
        return self.send_transaction(
            "dispense",
            (
                ContractBase.to_checksum_address(datatoken),
                amount,
                ContractBase.to_checksum_address(destination),
            ),
            from_wallet,
        )

    @enforce_types
    def owner_withdraw(self, datatoken: str, from_wallet) -> str:
        return self.send_transaction(
            "ownerWithdraw", (ContractBase.to_checksum_address(datatoken),), from_wallet
        )

    @enforce_types
    def dispense_tokens(self, datatoken: Datatoken, amount: int, consumer_wallet):
        self.dispense(
            datatoken=datatoken.address,
            amount=amount,
            destination=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )

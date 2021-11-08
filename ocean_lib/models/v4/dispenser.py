#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class DispenserV4(ContractBase):
    CONTRACT_NAME = "Dispenser"

    EVENT_DISPENSER_CREATED = "DispenserCreated"
    EVENT_DISPENSER_ACTIVATED = "DispenserActivated"
    EVENT_DISPENSER_DEACTIVATED = "DispenserDeactivated"
    EVENT_ALLOWED_SWAPPER_CHANGED = "DispenserAllowedSwapperChanged"
    EVENT_TOKENS_DISPENSED = "TokensDispensed"
    EVENT_OWNER_WITHDRAWED = "OwnerWithdrawed"

    @property
    def event_DispenserCreated(self):
        return self.events.DispenserCreated()

    @property
    def event_DispenserActivated(self):
        return self.events.DispenserActivated()

    @property
    def event_DispenserDeactivated(self):
        return self.events.DispenserDeactivated()

    @property
    def event_DispenserAllowedSwapperChanged(self):
        return self.events.DispenserAllowedSwapperChanged()

    @property
    def event_TokensDispensed(self):
        return self.events.TokensDispensed()

    @property
    def event_OwnerWithdrawed(self):
        return self.events.OwnerWithdrawed()

    def status(self, data_token: str) -> tuple:
        return self.contract.caller.status(data_token)

    def activate(
        self, data_token: str, max_tokens: int, max_balance: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "activate", (data_token, max_tokens, max_balance), from_wallet
        )

    def deactivate(self, data_token: str, from_wallet: Wallet) -> str:
        return self.send_transaction("deactivate", (data_token), from_wallet)

    def set_allowed_swapper(
        self, data_token: str, new_allowed_swapper: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setAllowedSwapper", (data_token, new_allowed_swapper), from_wallet
        )

    def dispense(
        self, data_token: str, amount: int, destination: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "dispense", (data_token, amount, destination), from_wallet
        )

    def owner_withdraw(self, data_token: str, from_wallet: Wallet) -> str:
        return self.send_transaction("ownerWithdraw", (data_token), from_wallet)

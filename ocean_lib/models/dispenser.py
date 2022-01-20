#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class Dispenser(ContractBase):
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

    def status(self, datatoken: str) -> tuple:
        return self.contract.caller.status(datatoken)

    def activate(
        self, datatoken: str, max_tokens: int, max_balance: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "activate", (datatoken, max_tokens, max_balance), from_wallet
        )

    def deactivate(self, datatoken: str, from_wallet: Wallet) -> str:
        return self.send_transaction("deactivate", (datatoken,), from_wallet)

    def set_allowed_swapper(
        self, datatoken: str, new_allowed_swapper: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setAllowedSwapper", (datatoken, new_allowed_swapper), from_wallet
        )

    def dispense(
        self, datatoken: str, amount: int, destination: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "dispense", (datatoken, amount, destination), from_wallet
        )

    def owner_withdraw(self, datatoken: str, from_wallet: Wallet) -> str:
        return self.send_transaction("ownerWithdraw", (datatoken,), from_wallet)

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
    def dispense_tokens(
        self, datatoken: Datatoken, amount: int, transaction_dict: dict
    ):
        self.dispense(
            datatoken.address,
            amount,
            transaction_dict["from"].address,
            transaction_dict,
        )

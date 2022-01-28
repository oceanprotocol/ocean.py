#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Union

from enforce_typing import enforce_types
from ocean_lib.models.models_structures import BPoolData
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class BFactory(ContractBase):
    CONTRACT_NAME = "BFactory"

    EVENT_BFACTORY_CREATED = "BPoolCreated"

    @property
    def event_BPoolCreated(self):
        return self.events.BPoolCreated()

    def new_bpool(
        self, bpool_data: Union[dict, tuple, BPoolData], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("newBPool", bpool_data, from_wallet)

    def is_pool_template(self, pool_template) -> bool:
        return self.contract.caller.isPoolTemplate(pool_template)

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.models.v4.models_structures import BPoolData
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC721Token(ContractBase):
    CONTRACT_NAME = "BFactory"

    EVENT_BFACTORY_CREATED = "BPoolCreated"

    @property
    def event_BPoolCreated(self):
        return self.events.BPoolCreated()

    def new_bpool(self, bpool_data: BPoolData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "newBPool",
            (
                bpool_data.controller,
                bpool_data.tokens,
                bpool_data.publisher,
                bpool_data.ss_params,
                bpool_data.swap_fees,
                bpool_data.market_fee_collector,
            ),
            from_wallet,
        )

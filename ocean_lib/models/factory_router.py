#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Union

from enforce_typing import enforce_types

from ocean_lib.models.bfactory import BFactory
from ocean_lib.structures.abi_tuples import Operations, Stakes
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class FactoryRouter(BFactory):
    CONTRACT_NAME = "FactoryRouter"
    EVENT_NEW_POOL = "NewPool"

    @property
    def event_NewPool(self):
        return self.events.NewPool()

    def router_owner(self) -> str:
        """Gets a router owner address."""
        return self.contract.caller.routerOwner()

    def is_pool_template(self, address: str) -> bool:
        return self.contract.caller.isPoolTemplate(address)

    def is_fixed_rate_contract(self, address: str) -> bool:
        return self.contract.caller.isFixedRateContract(address)

    def factory(self):
        return self.contract.caller.factory()

    def is_ss_contract(self, address: str):
        return self.contract.caller.isSSContract(address)

    def get_opc_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPCFee(base_token)

    def swap_ocean_fee(self) -> int:
        return self.contract.caller.swapOceanFee()

    def is_approved_token(self, ocean_address: str) -> bool:
        return self.contract.caller.isApprovedToken(ocean_address)

    def stake_batch(
        self, stakes: List[Union[dict, tuple, Stakes]], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("stakeBatch", (stakes,), from_wallet)

    def buy_dt_batch(
        self, operations: List[Union[dict, tuple, Operations]], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("buyDTBatch", (operations,), from_wallet)

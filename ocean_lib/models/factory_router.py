#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Tuple, Union

from enforce_typing import enforce_types

from ocean_lib.structures.abi_tuples import Operations, Stakes
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class FactoryRouter(ContractBase):
    CONTRACT_NAME = "FactoryRouter"
    EVENT_NEW_POOL = "NewPool"

    @property
    @enforce_types
    def event_NewPool(self):
        return self.events.NewPool()

    @enforce_types
    def router_owner(self) -> str:
        """Gets a router owner address."""
        return self.contract.caller.routerOwner()

    @enforce_types
    def factory(self) -> str:
        return self.contract.caller.factory()

    @enforce_types
    def swap_ocean_fee(self) -> int:
        return self.contract.caller.swapOceanFee()

    @enforce_types
    def swap_non_ocean_fee(self) -> int:
        return self.contract.caller.swapNonOceanFee()

    @enforce_types
    def is_approved_token(self, address: str) -> bool:
        return self.contract.caller.isApprovedToken(address)

    @enforce_types
    def is_ss_contract(self, address: str):
        return self.contract.caller.isSSContract(address)

    @enforce_types
    def is_fixed_rate_contract(self, address: str) -> bool:
        return self.contract.caller.isFixedRateContract(address)

    @enforce_types
    def is_dispenser_contract(self, address: str) -> bool:
        return self.contract.caller.isDispenserContract(address)

    @enforce_types
    def get_opc_collector(self) -> str:
        return self.contract.caller.getOPCCollector()

    @enforce_types
    def get_opc_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPCFee(base_token)

    @enforce_types
    def get_opc_fees(self) -> Tuple[int, int]:
        """Gets OP Community Fees for approved tokens and non approved tokens"""
        return self.contract.caller.getOPCFees()

    @enforce_types
    def get_opc_consume_fee(self) -> int:
        return self.contract.caller.getOPCConsumeFee()

    @enforce_types
    def get_opc_provider_fee(self) -> int:
        return self.contract.caller.getOPCProviderFee()

    @enforce_types
    def stake_batch(
        self, stakes: List[Union[dict, tuple, Stakes]], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("stakeBatch", (stakes,), from_wallet)

    @enforce_types
    def buy_dt_batch(
        self, operations: List[Union[dict, tuple, Operations]], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("buyDTBatch", (operations,), from_wallet)

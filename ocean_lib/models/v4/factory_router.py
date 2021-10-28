#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.v4.models_structures import (
    BPoolData,
    FixedData,
    DispenserData,
    Operations,
)
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

    def get_opf_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPFFee(base_token)

    def swap_ocean_fee(self) -> int:
        return self.contract.caller.swapOceanFee()

    def ocean_tokens(self, ocean_address: str) -> bool:
        return self.contract.caller.oceanTokens(ocean_address)

    def change_router_owner(self, new_router_owner: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "changeRouterOwner", (new_router_owner,), from_wallet
        )

    def add_ocean_token(self, ocean_token_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addOceanToken", (ocean_token_address,), from_wallet
        )

    def remove_ocean_token(self, ocean_token_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removeOceanToken", (ocean_token_address,), from_wallet
        )

    def add_ss_contract(self, new_ss_contract_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addSSContract", (new_ss_contract_address,), from_wallet
        )

    def add_factory(self, new_factory_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addFactory", (new_factory_address,), from_wallet)

    def add_fixed_rate_contract(
        self, new_fixed_contract: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "addFixedRateContract", (new_fixed_contract,), from_wallet
        )

    def add_dispenser_contract(self, new_dispenser: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addDispenserContract", (new_dispenser,), from_wallet
        )

    def update_opf_fee(self, new_swap_ocean_fee: int, from_wallet: Wallet) -> str:
        return self.send_transaction("updateOPFFee", (new_swap_ocean_fee,), from_wallet)

    def deploy_dispenser(
        self, dispenser_data: DispenserData, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "deployDispenser",
            (
                dispenser_data.dispenser_address,
                dispenser_data.data_token,
                dispenser_data.max_tokens,
                dispenser_data.max_balance,
                dispenser_data.owner,
                dispenser_data.allowed_swapper,
            ),
            from_wallet,
        )

    def deploy_pool(self, bpool_data: BPoolData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "deployPool",
            (
                bpool_data.tokens,
                bpool_data.ss_params,
                bpool_data.swap_fees,
                bpool_data.addresses,
            ),
            from_wallet,
        )

    def deploy_fixed_rate(self, fixed_data: FixedData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "deployFixedRate",
            (fixed_data.fixed_price_address, fixed_data.addresses, fixed_data.uints),
            from_wallet,
        )

    def add_pool_template(self, new_pool_template: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addPoolTemplate", (new_pool_template,), from_wallet
        )

    def remove_pool_template(self, pool_template: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removePoolTemplate", (pool_template,), from_wallet
        )

    def buy_dt_batch(self, operations: List[Operations], from_wallet: Wallet) -> str:
        return self.send_transaction("buyDTBatch", (operations,), from_wallet)

#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from typing import Union

from enforce_typing import enforce_types

from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.models_structures import DispenserData, OrderParams, ProviderFees
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC20Enterprise(ERC20Token):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    def buy_from_fre_and_order(
        self,
        order_params: Union[dict, tuple, OrderParams],
        fre_params: Union[dict, tuple],
        from_wallet: Wallet,
    ) -> str:
        # TODO: this will be handled in web3 py
        provider_fees = None
        if isinstance(order_params[2], ProviderFees):
            provider_fees = tuple(order_params[2])

        order_params = (order_params[0], order_params[1], provider_fees)

        return self.send_transaction(
            "buyFromFreAndOrder", (order_params, fre_params), from_wallet
        )

    def buy_from_dispenser_and_order(
        self,
        order_params: Union[dict, tuple, OrderParams],
        dispenser_address: str,
        from_wallet: Wallet,
    ) -> str:
        # TODO: this will be handled in web3 py
        provider_fees = None
        if isinstance(order_params[2], ProviderFees):
            provider_fees = tuple(order_params[2])

        order_params = (order_params[0], order_params[1], provider_fees)

        return self.send_transaction(
            "buyFromDispenserAndOrder", (order_params, dispenser_address), from_wallet
        )

    def create_dispenser(
        self, dispenser_data: Union[dict, tuple, DispenserData], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("createDispenser", dispenser_data, from_wallet)

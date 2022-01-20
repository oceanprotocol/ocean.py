#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from enforce_typing import enforce_types
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.models_structures import DispenserData
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC20Enterprise(ERC20Token):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    def buy_from_fre_and_order(
        self, order_params: tuple, fre_params: tuple, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "buyFromFreAndOrder", (order_params, fre_params), from_wallet
        )

    def buy_from_dispenser_and_order(
        self, order_params: tuple, dispenser_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "buyFromDispenserAndOrder", (order_params, dispenser_address), from_wallet
        )

    def create_dispenser(
        self, dispenser_data: DispenserData, with_mint: bool, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "createDispenser",
            (
                dispenser_data.dispenser_address,
                dispenser_data.max_tokens,
                dispenser_data.max_balance,
                with_mint,
                dispenser_data.allowed_swapper,
            ),
            from_wallet,
        )

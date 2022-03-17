#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

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
        self,
        datatoken_address: str,
        basetoken_address: str,
        rate: int,
        basetoken_decimals: int,
        vesting_amount: int,
        vesting_blocks: int,
        basetoken_amount: int,
        lp_swap_fee: int,
        market_swap_fee: int,
        controller: str,
        basetoken_sender: str,
        publisher_address: str,
        market_fee_collector: str,
        pool_template_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "newBPool",
            (
                [datatoken_address, basetoken_address],
                [
                    rate,
                    basetoken_decimals,
                    vesting_amount,
                    vesting_blocks,
                    basetoken_amount,
                ],
                [lp_swap_fee, market_swap_fee],
                [
                    controller,
                    basetoken_address,
                    basetoken_sender,
                    publisher_address,
                    market_fee_collector,
                    pool_template_address,
                ],
            ),
            from_wallet,
        )

    def is_pool_template(self, pool_template) -> bool:
        return self.contract.caller.isPoolTemplate(pool_template)

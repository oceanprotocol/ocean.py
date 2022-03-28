#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class BFactory(ContractBase):
    CONTRACT_NAME = "BFactory"

    EVENT_BFACTORY_CREATED = "BPoolCreated"

    @property
    def event_BPoolCreated(self):
        return self.events.BPoolCreated()

    @enforce_types
    def new_bpool(
        self,
        datatoken_address: str,
        base_token_address: str,
        rate: int,
        base_token_decimals: int,
        vesting_amount: int,
        vesting_blocks: int,
        base_token_amount: int,
        lp_swap_fee_amount: int,
        publish_market_swap_fee_amount: int,
        controller: str,
        base_token_sender: str,
        publisher_address: str,
        publish_market_swap_fee_collector: str,
        pool_template_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "newBPool",
            (
                [datatoken_address, base_token_address],
                [
                    rate,
                    base_token_decimals,
                    vesting_amount,
                    vesting_blocks,
                    base_token_amount,
                ],
                [lp_swap_fee_amount, publish_market_swap_fee_amount],
                [
                    controller,
                    base_token_address,
                    base_token_sender,
                    publisher_address,
                    publish_market_swap_fee_collector,
                    pool_template_address,
                ],
            ),
            from_wallet,
        )

    def is_pool_template(self, pool_template) -> bool:
        return self.contract.caller.isPoolTemplate(pool_template)

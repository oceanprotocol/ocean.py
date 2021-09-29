#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class FactoryRouter(ContractBase):

    #########################
    # Transaction methods
    @enforce_types
    def deployPool(
        self,
        controller: str,
        tokens: List[str],
        from_wallet: Wallet,
        ss_params: List[int],
        bt_sender: str,
        swap_fees: List[int],
        market_fee_collector: str,
    ) -> str:
        return self.send_transaction(
            "deployPool",
            (
                controller,
                tokens,
                from_wallet.address,
                ss_params,
                bt_sender,
                swap_fees,
                market_fee_collector,
            ),
            from_wallet,
        )

    @enforce_types
    def deployFixedRate(
        self,
        fixed_price_address: str,
        base_token: str,
        bt_decimals: int,
        exchange_rate: int,
        from_wallet,
        market_fee: int,
        market_fee_collector: str,
    ) -> str:
        return self.send_transaction(
            "deployFixedRate",
            (
                fixed_price_address,
                base_token,
                bt_decimals,
                exchange_rate,
                from_wallet.address,
                market_fee,
                market_fee_collector,
            ),
            from_wallet,
        )

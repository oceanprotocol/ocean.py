#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.v4.models_structures import BPoolData, FixedData
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class FactoryRouter(BFactory):
    def get_opf_fee(self, base_token: str) -> int:
        return self.contract.caller.getOPFFeee(base_token)

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
            (
                fixed_data.fixed_price_address,
                fixed_data.base_token,
                fixed_data.bt_decimals,
                fixed_data.exchange_rate,
                fixed_data.owner,
                fixed_data.market_fee,
                fixed_data.market_fee_collector,
            ),
            from_wallet,
        )

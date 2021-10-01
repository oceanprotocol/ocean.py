#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class IFixedRateExchange(ContractBase):

    #########################
    # Transaction methods
    @enforce_types
    def create(
        self,
        base_token: str,
        data_token: str,
        exchange_rate: int,
        from_wallet: Wallet,
        market_fee: int,
        market_fee_collector: str,
        opf_fee: int,
    ) -> str:
        return self.send_transaction(
            "create",
            (
                base_token,
                data_token,
                exchange_rate,
                from_wallet.address,
                market_fee,
                market_fee_collector,
                opf_fee,
            ),
            from_wallet,
        )

    @enforce_types
    def create_with_decimals(
        self,
        base_token: str,
        data_token: str,
        bt_decimals: int,
        dt_decimals: int,
        exchange_rate: int,
        from_wallet: Wallet,
        market_fee: int,
        market_fee_collector: str,
        opf_fee: int,
    ) -> str:
        return self.send_transaction(
            "createWithDecimals",
            (
                base_token,
                data_token,
                bt_decimals,
                dt_decimals,
                exchange_rate,
                from_wallet.address,
                market_fee,
                market_fee_collector,
                opf_fee,
            ),
            from_wallet,
        )

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class IPool(ContractBase):
    @enforce_types
    def get_data_token_address(self, from_wallet: Wallet) -> str:
        return self.send_transaction("getDataTokenAddress", from_wallet)

    @enforce_types
    def get_base_token_address(self, from_wallet: Wallet) -> str:
        return self.send_transaction("getBaseTokenAddress", from_wallet)

    @enforce_types
    def get_controller(self, from_wallet: Wallet) -> str:
        return self.send_transaction("getController", from_wallet)

    @enforce_types
    def setup(
        self,
        data_token: str,
        data_token_amount: int,
        data_token_weight: int,
        base_token: str,
        base_token_amount: int,
        base_token_weight: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setup",
            (
                data_token,
                data_token_amount,
                data_token_weight,
                base_token,
                base_token_amount,
                base_token_weight,
            ),
            from_wallet,
        )

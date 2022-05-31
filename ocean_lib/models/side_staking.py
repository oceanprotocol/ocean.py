#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class SideStaking(ContractBase):
    CONTRACT_NAME = "SideStaking"

    @enforce_types
    def get_datatoken_circulating_supply(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenCirculatingSupply(datatoken)

    @enforce_types
    def get_datatoken_current_circulating_supply(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenCurrentCirculatingSupply(datatoken)

    @enforce_types
    def get_publisher_address(self, datatoken: str) -> str:
        return self.contract.caller.getPublisherAddress(datatoken)

    @enforce_types
    def get_base_token_address(self, datatoken: str) -> str:
        return self.contract.caller.getBaseTokenAddress(datatoken)

    @enforce_types
    def get_pool_address(self, datatoken: str) -> str:
        return self.contract.caller.getPoolAddress(datatoken)

    @enforce_types
    def get_base_token_balance(self, datatoken: str) -> int:
        return self.contract.caller.getBaseTokenBalance(datatoken)

    @enforce_types
    def get_datatoken_balance(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenBalance(datatoken)

    @enforce_types
    def notify_finalize(
        self, datatoken: str, decimals: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "notifyFinalize", (datatoken, decimals), from_wallet
        )

    @enforce_types
    def set_pool_swap_fee(
        self,
        datatoken: str,
        pool_address: str,
        lp_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setPoolSwapFee", (datatoken, pool_address, lp_swap_fee_amount), from_wallet
        )

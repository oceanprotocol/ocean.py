#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class SideStaking(ContractBase):
    CONTRACT_NAME = "SideStaking"

    def get_data_token_circulating_supply(self, data_token: str) -> int:
        return self.contract.caller.getDataTokenCirculatingSupply(data_token)

    def get_publisher_address(self, data_token: str) -> str:
        return self.contract.caller.getPublisherAddress(data_token)

    def get_base_token_address(self, data_token: str) -> str:
        return self.contract.caller.getBaseTokenAddress(data_token)

    def get_pool_address(self, data_token: str) -> str:
        return self.contract.caller.getPoolAddress(data_token)

    def get_base_token_balance(self, data_token: str) -> int:
        return self.contract.caller.getBaseTokenBalance(data_token)

    def get_data_token_balance(self, data_token: str) -> int:
        return self.contract.caller.getDataTokenBalance(data_token)

    def get_vesting_end_block(self, data_token: str) -> int:
        return self.contract.caller.getvestingEndBlock(data_token)

    def get_vesting_amount(self, data_token: str) -> int:
        return self.contract.caller.getvestingAmount(data_token)

    def get_vesting_last_block(self, data_token: str) -> int:
        return self.contract.caller.getvestingLastBlock(data_token)

    def get_vesting_amount_so_far(self, data_token: str) -> int:
        return self.contract.caller.getvestingAmountSoFar(data_token)

    def can_stake(self, data_token: str, stake_token: str, amount: int) -> bool:
        return self.contract.caller.canStake(data_token, stake_token, amount)

    def stake(
        self, data_token: str, stake_token: str, amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "Stake", (data_token, stake_token, amount), from_wallet
        )

    def can_unstake(
        self, data_token: str, stake_token: str, liquidity_pool_token_in: int
    ) -> bool:
        return self.contract.caller.canUnStake(
            data_token, stake_token, liquidity_pool_token_in
        )

    def unstake(
        self,
        data_token: str,
        stake_token: str,
        dtAmountIn: int,
        poolAmountOut: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "UnStake", (data_token, stake_token, dtAmountIn, poolAmountOut), from_wallet
        )

    def notify_finalize(
        self, data_token: str, decimals: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "notifyFinalize", (data_token, decimals), from_wallet
        )

    def get_vesting(self, data_token: str, from_wallet: Wallet) -> str:
        return self.send_transaction("getVesting", (data_token,), from_wallet)

#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class SideStaking(ContractBase):
    CONTRACT_NAME = "SideStaking"
    EVENT_VESTING = "Vesting"
    EVENT_VESTING_CREATED = "VestingCreated"

    @property
    def event_Vesting(self):
        return self.events.Vesting()

    @property
    def event_VestingCreated(self):
        return self.events.VestingCreated()

    def get_available_vesting(self, datatoken: str) -> int:
        return self.contract.caller.getAvailableVesting(datatoken)

    def get_datatoken_circulating_supply(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenCirculatingSupply(datatoken)

    def get_datatoken_current_circulating_supply(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenCurrentCirculatingSupply(datatoken)

    def get_publisher_address(self, datatoken: str) -> str:
        return self.contract.caller.getPublisherAddress(datatoken)

    def get_base_token_address(self, datatoken: str) -> str:
        return self.contract.caller.getBaseTokenAddress(datatoken)

    def get_pool_address(self, datatoken: str) -> str:
        return self.contract.caller.getPoolAddress(datatoken)

    def get_base_token_balance(self, datatoken: str) -> int:
        return self.contract.caller.getBaseTokenBalance(datatoken)

    def get_datatoken_balance(self, datatoken: str) -> int:
        return self.contract.caller.getDatatokenBalance(datatoken)

    def get_vesting_end_block(self, datatoken: str) -> int:
        return self.contract.caller.getvestingEndBlock(datatoken)

    def get_vesting_amount(self, datatoken: str) -> int:
        return self.contract.caller.getvestingAmount(datatoken)

    def get_vesting_last_block(self, datatoken: str) -> int:
        return self.contract.caller.getvestingLastBlock(datatoken)

    def get_vesting_amount_so_far(self, datatoken: str) -> int:
        return self.contract.caller.getvestingAmountSoFar(datatoken)

    def notify_finalize(
        self, datatoken: str, decimals: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "notifyFinalize", (datatoken, decimals), from_wallet
        )

    def get_vesting(self, datatoken: str, from_wallet: Wallet) -> str:
        return self.send_transaction("getVesting", (datatoken,), from_wallet)

    def set_pool_swap_fee(
        self, datatoken: str, pool_address: str, swap_fee: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setPoolSwapFee", (datatoken, pool_address, swap_fee), from_wallet
        )

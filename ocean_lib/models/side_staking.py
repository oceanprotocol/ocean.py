#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from eth_typing import HexStr

from ocean_lib.models.erc20_token import ERC20Token
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

    def can_stake(self, datatoken: str, amount: int) -> bool:
        return self.contract.caller.canStake(datatoken, amount)

    def stake(self, datatoken: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("Stake", (datatoken, amount), from_wallet)

    def can_unstake(self, datatoken: str, liquidity_pool_token_in: int) -> bool:
        return self.contract.caller.canUnStake(datatoken, liquidity_pool_token_in)

    def unstake(
        self,
        datatoken: str,
        dt_amount_in: int,
        pool_amount_out: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "UnStake", (datatoken, dt_amount_in, pool_amount_out), from_wallet
        )

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

    def check_vesting_created_event(
        self,
        block_number: int,
        erc20_token: ERC20Token,
        vested_blocks: int,
        vesting_amount: int,
    ) -> None:
        vesting_created_event = self.get_event_log(
            SideStaking.EVENT_VESTING_CREATED,
            block_number,
            self.web3.eth.block_number,
            None,
        )
        assert vesting_created_event, "Cannot find event VestingCreated."
        assert vesting_created_event[0].args.datatokenAddress == erc20_token.address
        assert (
            vesting_created_event[0].args.publisherAddress
            == erc20_token.get_payment_collector()
        )
        assert (
            vesting_created_event[0].args.vestingEndBlock
            == vested_blocks + block_number
        )
        assert vesting_created_event[0].args.totalVestingAmount == vesting_amount

    def get_amount_vested_from_event(
        self, tx_hash: HexStr, erc20_token: ERC20Token, from_wallet: Wallet
    ) -> int:
        tx_result = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        vesting_event = self.get_event_log(
            SideStaking.EVENT_VESTING,
            tx_result.blockNumber,
            self.web3.eth.block_number,
            None,
        )
        assert vesting_event[0].args.datatokenAddress == erc20_token.address
        assert (
            vesting_event[0].args.publisherAddress
            == erc20_token.get_payment_collector()
        )
        assert vesting_event[0].args.caller == from_wallet.address

        return vesting_event[0].args.amountVested

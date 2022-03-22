#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Optional, Tuple

from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class RolesERC20(IntEnum):
    MINTER = 0
    PAYMENT_MANAGER = 1


@enforce_types
class ERC20Token(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    EVENT_ORDER_STARTED = "OrderStarted"
    EVENT_ORDER_REUSED = "OrderReused"
    EVENT_ORDER_EXECUTED = "OrderExecuted"
    EVENT_PUBLISH_MARKET_FEE_CHANGED = "PublishMarketFeeChanged"
    EVENT_CONSUME_MARKET_FEE = "ConsumeMarketFee"
    EVENT_PROVIDER_FEE = "ProviderFee"
    EVENT_MINTER_PROPOSED = "MinterProposed"
    EVENT_MINTER_APPROVED = "MinterApproved"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"

    @property
    def event_OrderStarted(self):
        return self.events.OrderStarted()

    @property
    def event_OrderReused(self):
        return self.events.OrderReused()

    @property
    def event_OrderExecuted(self):
        return self.events.OrderExecuted()

    @property
    def event_PublishMarketFeeChanged(self):
        return self.events.PublishMarketFeeChanged()

    @property
    def event_ConsumeMarketFee(self):
        return self.events.ConsumeMarketFee()

    @property
    def event_ProviderFee(self):
        return self.events.ProviderFee()

    @property
    def event_MinterProposed(self):
        return self.events.MinterProposed()

    @property
    def event_MinterApproved(self):
        return self.events.MinterApproved()

    @property
    def event_NewPool(self):
        return self.events.NewPool()

    @property
    def event_NewFixedRate(self):
        return self.events.NewFixedRate()

    def deploy_pool(
        self,
        rate: int,
        basetoken_decimals: int,
        vesting_amount: int,
        vested_blocks: int,
        initial_liq: int,
        lp_swap_fee: int,
        market_swap_fee: int,
        ss_contract: str,
        basetoken_address: str,
        basetoken_sender: str,
        publisher_address: str,
        market_fee_collector: str,
        pool_template_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "deployPool",
            (
                [rate, basetoken_decimals, vesting_amount, vested_blocks, initial_liq],
                [lp_swap_fee, market_swap_fee],
                [
                    ss_contract,
                    basetoken_address,
                    basetoken_sender,
                    publisher_address,
                    market_fee_collector,
                    pool_template_address,
                ],
            ),
            from_wallet,
        )

    def create_fixed_rate(
        self,
        fixed_price_address: str,
        basetoken_address: str,
        owner: str,
        market_fee_collector: str,
        allowed_swapper: str,
        basetoken_decimals: int,
        datatoken_decimals: int,
        fixed_rate: int,
        market_fee: int,
        with_mint: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createFixedRate",
            (
                fixed_price_address,
                [basetoken_address, owner, market_fee_collector, allowed_swapper],
                [
                    basetoken_decimals,
                    datatoken_decimals,
                    fixed_rate,
                    market_fee,
                    with_mint,
                ],
            ),
            from_wallet,
        )

    def create_dispenser(
        self,
        dispenser_address: str,
        max_tokens: int,
        max_balance: int,
        with_mint: bool,
        allowed_swapper: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createDispenser",
            (dispenser_address, max_tokens, max_balance, with_mint, allowed_swapper),
            from_wallet,
        )

    def mint(self, account_address: str, value: int, from_wallet: Wallet) -> str:
        return self.send_transaction("mint", (account_address, value), from_wallet)

    def check_provider_fee(
        self,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: int,
        v: str,
        r: str,
        s: str,
        valid_until: int,
        provider_data: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "checkProviderFee",
            (
                provider_fee_address,
                provider_fee_token,
                provider_fee_amount,
                v,
                r,
                s,
                valid_until,
                provider_data,
            ),
            from_wallet,
        )

    def start_order(
        self,
        consumer: str,
        service_index: int,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: int,
        v: str,
        r: str,
        s: str,
        valid_until: int,
        provider_data: bytes,
        consumer_market_fee_address: str,
        consumer_market_fee_token: str,
        consumer_market_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startOrder",
            (
                consumer,
                service_index,
                (
                    provider_fee_address,
                    provider_fee_token,
                    provider_fee_amount,
                    v,
                    r,
                    s,
                    valid_until,
                    provider_data,
                ),
                (
                    consumer_market_fee_address,
                    consumer_market_fee_token,
                    consumer_market_fee_amount,
                ),
            ),
            from_wallet,
        )

    def reuse_order(
        self,
        order_tx_id: str,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: int,
        v: str,
        r: str,
        s: str,
        valid_until: int,
        provider_data: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "reuseOrder",
            (
                order_tx_id,
                (
                    provider_fee_address,
                    provider_fee_token,
                    provider_fee_amount,
                    v,
                    r,
                    s,
                    valid_until,
                    provider_data,
                ),
            ),
            from_wallet,
        )

    def order_executed(
        self,
        order_tx_id: str,
        provider_data: bytes,
        provider_signature: bytes,
        consumer_data: bytes,
        consumer_signature: bytes,
        consumer: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "orderExecuted",
            (
                order_tx_id,
                provider_data,
                provider_signature,
                consumer_data,
                consumer_signature,
                consumer,
            ),
            from_wallet,
        )

    def transfer(self, to: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("transfer", (to, amount), from_wallet)

    def allowance(self, owner_address: str, spender_address: str) -> int:
        return self.contract.caller.allowance(owner_address, spender_address)

    def approve(self, spender: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("approve", (spender, amount), from_wallet)

    def transferFrom(
        self, from_address: str, to_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, amount), from_wallet
        )

    def burn(self, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("burn", (amount,), from_wallet)

    def burn_from(self, from_address: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("burnFrom", (from_address, amount), from_wallet)

    def is_minter(self, account: str) -> bool:
        return self.contract.caller.isMinter(account)

    def add_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addMinter", (minter_address,), from_wallet)

    def remove_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeMinter", (minter_address,), from_wallet)

    def add_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addPaymentManager", (fee_manager,), from_wallet)

    def remove_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removePaymentManager", (fee_manager,), from_wallet
        )

    def set_data(self, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setData", (data,), from_wallet)

    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    def clean_from_721(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanFrom721", (), from_wallet)

    def set_payment_collector(
        self, fee_collector_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setPaymentCollector", (fee_collector_address,), from_wallet
        )

    def get_publishing_market_fee(self) -> tuple:
        return self.contract.caller.getPublishingMarketFee()

    def set_publishing_market_fee(
        self,
        publish_market_fee_address: str,
        publish_market_fee_token: str,
        publish_market_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setPublishingMarketFee",
            (
                publish_market_fee_address,
                publish_market_fee_token,
                publish_market_fee_amount,
            ),
            from_wallet,
        )

    def get_id(self) -> int:
        return self.contract.caller.getId()

    def token_name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def get_erc721_address(self) -> str:
        return self.contract.caller.getERC721Address()

    def decimals(self) -> int:
        return self.contract.caller.decimals()

    def cap(self) -> int:
        return self.contract.caller.cap()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def permit(
        self,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "permit",
            (owner_address, spender_address, value, deadline, v, r, s),
            from_wallet,
        )

    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    def get_uint_length(self, array: List[int]) -> int:
        return self.contract.caller.getUintLength(array)

    def get_bytes_length(self, array: List[bytes]) -> int:
        return self.contract.caller.getBytesLength(array)

    def get_payment_collector(self) -> str:
        return self.contract.caller.getPaymentCollector()

    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    def get_permissions(self, user: str) -> list:
        return self.contract.caller.getPermissions(user)

    def permissions(self, user: str) -> list:
        return self.contract.caller.permissions(user)

    def get_total_supply(self) -> int:
        return self.contract.caller.totalSupply()

    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
        from_all_tokens: bool = False,
    ) -> Tuple:
        topic0 = self.get_event_signature(self.EVENT_ORDER_STARTED)
        topics = [topic0]
        if consumer_address:
            topic1 = f"0x000000000000000000000000{consumer_address[2:].lower()}"
            topics = [topic0, None, topic1]

        argument_filters = {"topics": topics}

        logs = self.getLogs(
            self.events.OrderStarted(),
            argument_filters=argument_filters,
            fromBlock=from_block,
            toBlock=to_block,
            from_all_addresses=from_all_tokens,
        )
        return logs


class MockERC20(ERC20Token):
    CONTRACT_NAME = "MockERC20"


class MockOcean(ERC20Token):
    CONTRACT_NAME = "MockOcean"

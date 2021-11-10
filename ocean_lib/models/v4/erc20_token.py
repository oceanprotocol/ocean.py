#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List

from enforce_typing import enforce_types

from ocean_lib.models.v4.models_structures import PoolData, FixedData, DispenserData
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class RolesERC20(IntEnum):
    MINTER = 0
    FEE_MANAGER = 1


@enforce_types
class ERC20Token(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10 ** 18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    EVENT_ORDER_STARTED = "OrderStarted"
    EVENT_MINTER_PROPOSED = "MinterProposed"
    EVENT_MINTER_APPROVED = "MinterApproved"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"

    @property
    def event_OrderStarted(self):
        return self.events.OrderStarted()

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

    def initialize(
        self,
        strings: List[str],
        addresses: List[str],
        factory_addresses: List[str],
        uints: List[int],
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (strings, addresses, factory_addresses, uints, bytess),
            from_wallet,
        )

    def deploy_pool(self, pool_data: PoolData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "deployPool",
            (
                pool_data.ss_params,
                pool_data.swap_fees,
                pool_data.addresses,
            ),
            from_wallet,
        )

    def create_fixed_rate(self, fixed_data: FixedData, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "createFixedRate",
            (fixed_data.fixed_price_address, fixed_data.addresses, fixed_data.uints),
            from_wallet,
        )

    def create_dispenser(
        self, dispenser_data: DispenserData, with_mint: bool, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "createDispenser",
            (
                dispenser_data.dispenser_address,
                dispenser_data.max_tokens,
                dispenser_data.max_balance,
                with_mint,
                dispenser_data.allowed_swapper,
            ),
            from_wallet,
        )

    def mint(self, account_address: str, value: int, from_wallet: Wallet) -> str:
        return self.send_transaction("mint", (account_address, value), from_wallet)

    def start_order(
        self,
        consumer: str,
        amount: int,
        service_id: int,
        mrkt_fee_collector: str,
        fee_token: str,
        fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startOrder",
            (consumer, amount, service_id, mrkt_fee_collector, fee_token, fee_amount),
            from_wallet,
        )

    def start_multiple_order(
        self,
        consumers: List[str],
        amounts: List[int],
        service_ids: List[int],
        mrkt_fee_collectors: List[str],
        fee_tokens: List[str],
        fee_amounts: List[int],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startMultipleOrder",
            (
                consumers,
                amounts,
                service_ids,
                mrkt_fee_collectors,
                fee_tokens,
                fee_amounts,
            ),
            from_wallet,
        )

    def finish_order(
        self,
        order_tx_id: str,
        consumer: str,
        amount: int,
        service_id: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "finishOrder", (order_tx_id, consumer, amount, service_id), from_wallet
        )

    def finish_multiple_order(
        self,
        order_tx_ids: List[str],
        consumers: List[str],
        amounts: List[int],
        service_ids: List[int],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "finishMultipleOrder",
            (order_tx_ids, consumers, amounts, service_ids),
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

    def add_fee_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addFeeManager", (fee_manager,), from_wallet)

    def remove_fee_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeFeeManager", (fee_manager,), from_wallet)

    def set_data(self, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setData", (data,), from_wallet)

    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    def clean_from_721(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanFrom721", (), from_wallet)

    def set_fee_collector(self, fee_collector_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "setFeeCollector", (fee_collector_address,), from_wallet
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

    def permissions(self, account: str) -> list:
        return self.contract.caller.permissions(account)

    def get_id(self) -> int:
        return self.contract.caller.getId()

    def name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def decimals(self) -> int:
        return self.contract.caller.decimals()

    def cap(self) -> int:
        return self.contract.caller.cap()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def calculate_fee(self, amount: int, fee_percentage: int) -> int:
        return self.contract.caller.calculateFee(amount, fee_percentage)

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

    def get_fee_collector(self) -> str:
        return self.contract.caller.getFeeCollector()

    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    def get_permissions(self, user: str) -> list:
        return self.contract.caller.permissions(user)

    def get_total_supply(self) -> int:
        return self.contract.caller.totalSupply()


class MockERC20(ERC20Token):
    CONTRACT_NAME = "MockERC20"


class MockOcean(ERC20Token):
    CONTRACT_NAME = "MockOcean"

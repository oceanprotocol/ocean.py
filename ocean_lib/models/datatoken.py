#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Optional, Tuple, Union

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class DatatokenRoles(IntEnum):
    MINTER = 0
    PAYMENT_MANAGER = 1


class Datatoken(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    EVENT_ORDER_STARTED = "OrderStarted"
    EVENT_ORDER_REUSED = "OrderReused"
    EVENT_ORDER_EXECUTED = "OrderExecuted"
    EVENT_PUBLISH_MARKET_FEE_CHANGED = "PublishMarketFeeChanged"
    EVENT_PUBLISH_MARKET_FEE = "PublishMarketFee"
    EVENT_CONSUME_MARKET_FEE = "ConsumeMarketFee"
    EVENT_PROVIDER_FEE = "ProviderFee"
    EVENT_MINTER_PROPOSED = "MinterProposed"
    EVENT_MINTER_APPROVED = "MinterApproved"
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
    def event_PublishMarketFee(self):
        return self.events.PublishMarketFee()

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
    def event_NewFixedRate(self):
        return self.events.NewFixedRate()

    @enforce_types
    def router(self) -> str:
        return self.contract.caller.router()

    @enforce_types
    def create_fixed_rate(
        self,
        fixed_price_address: str,
        base_token_address: str,
        owner: str,
        publish_market_swap_fee_collector: str,
        allowed_swapper: str,
        base_token_decimals: int,
        datatoken_decimals: int,
        fixed_rate: int,
        publish_market_swap_fee_amount: int,
        with_mint: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createFixedRate",
            (
                ContractBase.to_checksum_address(fixed_price_address),
                [
                    ContractBase.to_checksum_address(base_token_address),
                    ContractBase.to_checksum_address(owner),
                    ContractBase.to_checksum_address(publish_market_swap_fee_collector),
                    ContractBase.to_checksum_address(allowed_swapper),
                ],
                [
                    base_token_decimals,
                    datatoken_decimals,
                    fixed_rate,
                    publish_market_swap_fee_amount,
                    with_mint,
                ],
            ),
            from_wallet,
        )

    @enforce_types
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
            (
                ContractBase.to_checksum_address(dispenser_address),
                max_tokens,
                max_balance,
                with_mint,
                ContractBase.to_checksum_address(allowed_swapper),
            ),
            from_wallet,
        )

    @enforce_types
    def mint(self, account_address: str, value: int, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "mint",
            (ContractBase.to_checksum_address(account_address), value),
            from_wallet,
        )

    @enforce_types
    def check_provider_fee(
        self,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: Union[int, str],
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        valid_until: int,
        provider_data: Union[str, bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "checkProviderFee",
            (
                ContractBase.to_checksum_address(provider_fee_address),
                ContractBase.to_checksum_address(provider_fee_token),
                int(provider_fee_amount),
                v,
                r,
                s,
                valid_until,
                provider_data,
            ),
            from_wallet,
        )

    @enforce_types
    def start_order(
        self,
        consumer: str,
        service_index: int,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: Union[int, str],
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        valid_until: int,
        provider_data: Union[str, bytes],
        consume_market_order_fee_address: str,
        consume_market_order_fee_token: str,
        consume_market_order_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startOrder",
            (
                ContractBase.to_checksum_address(consumer),
                service_index,
                (
                    ContractBase.to_checksum_address(provider_fee_address),
                    ContractBase.to_checksum_address(provider_fee_token),
                    int(provider_fee_amount),
                    v,
                    r,
                    s,
                    valid_until,
                    provider_data,
                ),
                (
                    ContractBase.to_checksum_address(consume_market_order_fee_address),
                    ContractBase.to_checksum_address(consume_market_order_fee_token),
                    consume_market_order_fee_amount,
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def reuse_order(
        self,
        order_tx_id: Union[str, bytes],
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: Union[int, str],
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        valid_until: int,
        provider_data: Union[str, bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "reuseOrder",
            (
                order_tx_id,
                (
                    ContractBase.to_checksum_address(provider_fee_address),
                    ContractBase.to_checksum_address(provider_fee_token),
                    int(provider_fee_amount),
                    v,
                    r,
                    s,
                    valid_until,
                    provider_data,
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def order_executed(
        self,
        order_tx_id: Union[str, bytes],
        provider_data: Union[str, bytes],
        provider_signature: Union[str, bytes],
        consumer_data: Union[str, bytes],
        consumer_signature: Union[str, bytes],
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
                ContractBase.to_checksum_address(consumer),
            ),
            from_wallet,
        )

    @enforce_types
    def transfer(self, to: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "transfer", (ContractBase.to_checksum_address(to), amount), from_wallet
        )

    @enforce_types
    def allowance(self, owner_address: str, spender_address: str) -> int:
        return self.contract.caller.allowance(
            ContractBase.to_checksum_address(owner_address),
            ContractBase.to_checksum_address(spender_address),
        )

    @enforce_types
    def approve(self, spender: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "approve", (ContractBase.to_checksum_address(spender), amount), from_wallet
        )

    @enforce_types
    def transferFrom(
        self, from_address: str, to_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom",
            (
                ContractBase.to_checksum_address(from_address),
                ContractBase.to_checksum_address(to_address),
                amount,
            ),
            from_wallet,
        )

    @enforce_types
    def burn(self, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("burn", (amount,), from_wallet)

    @enforce_types
    def burn_from(self, from_address: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "burnFrom",
            (ContractBase.to_checksum_address(from_address), amount),
            from_wallet,
        )

    @enforce_types
    def is_minter(self, account: str) -> bool:
        return self.contract.caller.isMinter(ContractBase.to_checksum_address(account))

    @enforce_types
    def add_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addMinter",
            (ContractBase.to_checksum_address(minter_address),),
            from_wallet,
        )

    @enforce_types
    def remove_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removeMinter",
            (ContractBase.to_checksum_address(minter_address),),
            from_wallet,
        )

    @enforce_types
    def add_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "addPaymentManager",
            (ContractBase.to_checksum_address(fee_manager),),
            from_wallet,
        )

    @enforce_types
    def remove_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removePaymentManager",
            (ContractBase.to_checksum_address(fee_manager),),
            from_wallet,
        )

    @enforce_types
    def set_data(self, data: str, from_wallet: Wallet) -> str:
        return self.send_transaction("setData", (data,), from_wallet)

    @enforce_types
    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    @enforce_types
    def clean_from_721(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanFrom721", (), from_wallet)

    @enforce_types
    def set_payment_collector(
        self, publish_market_order_fee_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setPaymentCollector",
            (ContractBase.to_checksum_address(publish_market_order_fee_address),),
            from_wallet,
        )

    @enforce_types
    def get_publishing_market_fee(self) -> tuple:
        return self.contract.caller.getPublishingMarketFee()

    @enforce_types
    def set_publishing_market_fee(
        self,
        publish_market_order_fee_address: str,
        publish_market_order_fee_token: str,
        publish_market_order_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setPublishingMarketFee",
            (
                ContractBase.to_checksum_address(publish_market_order_fee_address),
                ContractBase.to_checksum_address(publish_market_order_fee_token),
                publish_market_order_fee_amount,
            ),
            from_wallet,
        )

    @enforce_types
    def get_id(self) -> int:
        return self.contract.caller.getId()

    @enforce_types
    def token_name(self) -> str:
        return self.contract.caller.name()

    @enforce_types
    def symbol(self) -> str:
        return self.contract.caller.symbol()

    @enforce_types
    def get_erc721_address(self) -> str:
        return self.contract.caller.getERC721Address()

    @enforce_types
    def decimals(self) -> int:
        return self.contract.caller.decimals()

    @enforce_types
    def cap(self) -> int:
        return self.contract.caller.cap()

    @enforce_types
    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    @enforce_types
    def permit(
        self,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "permit",
            (
                ContractBase.to_checksum_address(owner_address),
                ContractBase.to_checksum_address(spender_address),
                value,
                deadline,
                v,
                r,
                s,
            ),
            from_wallet,
        )

    @enforce_types
    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    @enforce_types
    def get_uint_length(self, array: List[int]) -> int:
        return self.contract.caller.getUintLength(array)

    @enforce_types
    def get_bytes_length(self, array: List[bytes]) -> int:
        return self.contract.caller.getBytesLength(array)

    @enforce_types
    def get_payment_collector(self) -> str:
        return self.contract.caller.getPaymentCollector()

    @enforce_types
    def get_fixed_rates(self) -> List[Tuple[str, bytes]]:
        return self.contract.caller.getFixedRates()

    @enforce_types
    def get_dispensers(self) -> List[str]:
        return self.contract.caller.getDispensers()

    @enforce_types
    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    @enforce_types
    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    @enforce_types
    def get_permissions(self, user: str) -> list:
        return self.contract.caller.getPermissions(
            ContractBase.to_checksum_address(user)
        )

    @enforce_types
    def permissions(self, user: str) -> list:
        return self.contract.caller.permissions(ContractBase.to_checksum_address(user))

    @enforce_types
    def get_total_supply(self) -> int:
        return self.contract.caller.totalSupply()

    @enforce_types
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


class MockERC20(Datatoken):
    CONTRACT_NAME = "MockERC20"


class MockOcean(Datatoken):
    CONTRACT_NAME = "MockOcean"

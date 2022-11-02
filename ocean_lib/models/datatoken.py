#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Optional, Tuple, Union

from brownie.network.state import Chain
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase


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
        from_wallet,
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
        from_wallet,
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
        from_wallet,
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

    def set_data(self, data: str, from_wallet) -> str:
        return self.send_transaction("setData", (data,), from_wallet)

    @enforce_types
    def clean_permissions(self, from_wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    @enforce_types
    def clean_from_721(self, from_wallet) -> str:
        return self.send_transaction("cleanFrom721", (), from_wallet)

    @enforce_types
    def set_payment_collector(
        self, publish_market_order_fee_address: str, from_wallet
    ) -> str:
        return self.send_transaction(
            "setPaymentCollector",
            (ContractBase.to_checksum_address(publish_market_order_fee_address),),
            from_wallet,
        )

    @enforce_types
    def get_publishing_market_fee(self) -> tuple:
        return self.contract.getPublishingMarketFee()

    @enforce_types
    def set_publishing_market_fee(
        self,
        publish_market_order_fee_address: str,
        publish_market_order_fee_token: str,
        publish_market_order_fee_amount: int,
        from_wallet,
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
        return self.contract.getId()

    @enforce_types
    def token_name(self) -> str:
        return self.contract.name()

    @enforce_types
    def get_erc721_address(self) -> str:
        return self.contract.getERC721Address()

    @enforce_types
    def is_initialized(self) -> bool:
        return self.contract.isInitialized()

    @enforce_types
    def get_address_length(self, array: List[str]) -> int:
        return self.contract.getAddressLength(array)

    @enforce_types
    def get_uint_length(self, array: List[int]) -> int:
        return self.contract.getUintLength(array)

    @enforce_types
    def get_bytes_length(self, array: List[bytes]) -> int:
        return self.contract.getBytesLength(array)

    @enforce_types
    def get_payment_collector(self) -> str:
        return self.contract.getPaymentCollector()

    @enforce_types
    def get_fixed_rates(self) -> List[Tuple[str, bytes]]:
        return self.contract.getFixedRates()

    @enforce_types
    def get_dispensers(self) -> List[str]:
        return self.contract.getDispensers()

    @enforce_types
    def balanceOf(self, account: str) -> int:
        return self.contract.balanceOf(account)

    @enforce_types
    def withdraw(self, from_wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    @enforce_types
    def get_permissions(self, user: str) -> list:
        return self.contract.getPermissions(ContractBase.to_checksum_address(user))

    @enforce_types
    def get_total_supply(self) -> int:
        return self.contract.totalSupply()

    @enforce_types
    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
    ) -> Tuple:
        chain = Chain()
        to_block = to_block if to_block != "latest" else chain[-1].number

        return self.contract.events.get_sequence(
            from_block, to_block, self.EVENT_ORDER_STARTED
        )


class MockERC20(Datatoken):
    CONTRACT_NAME = "MockERC20"


class MockOcean(Datatoken):
    CONTRACT_NAME = "MockOcean"

#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import Optional, Tuple, Union

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
        transaction_parameters: dict,
    ) -> str:
        return self.contract.createFixedRate(
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
            transaction_parameters,
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
        transaction_parameters: dict,
    ) -> str:
        return self.contract.startOrder(
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
            transaction_parameters,
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
        transaction_parameters: dict,
    ) -> str:
        return self.contract.reuseOrder(
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
            transaction_parameters,
        )

    @enforce_types
    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
    ) -> Tuple:
        chain = Chain()
        to_block = to_block if to_block != "latest" else chain[-1].number

        return self.contract.events.get_sequence(from_block, to_block, "OrderStarted")


class MockERC20(Datatoken):
    CONTRACT_NAME = "MockERC20"


class MockOcean(Datatoken):
    CONTRACT_NAME = "MockOcean"

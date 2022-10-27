#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Union

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class DatatokenEnterprise(Datatoken):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    @enforce_types
    def buy_from_fre_and_order(
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
        exchange_contract: str,
        exchange_id: bytes,
        max_base_token_amount: int,
        consume_market_swap_fee_amount: int,
        consume_market_swap_fee_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "buyFromFreAndOrder",
            (
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
                        ContractBase.to_checksum_address(
                            consume_market_order_fee_address
                        ),
                        ContractBase.to_checksum_address(
                            consume_market_order_fee_token
                        ),
                        consume_market_order_fee_amount,
                    ),
                ),
                (
                    ContractBase.to_checksum_address(exchange_contract),
                    exchange_id,
                    max_base_token_amount,
                    consume_market_swap_fee_amount,
                    ContractBase.to_checksum_address(consume_market_swap_fee_address),
                ),
            ),
            from_wallet,
        )

    @enforce_types
    def buy_from_dispenser_and_order(
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
        dispenser_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "buyFromDispenserAndOrder",
            (
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
                        ContractBase.to_checksum_address(
                            consume_market_order_fee_address
                        ),
                        ContractBase.to_checksum_address(
                            consume_market_order_fee_token
                        ),
                        consume_market_order_fee_amount,
                    ),
                ),
                ContractBase.to_checksum_address(dispenser_address),
            ),
            from_wallet,
        )

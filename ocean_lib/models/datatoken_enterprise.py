#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Any

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address


class DatatokenEnterprise(Datatoken):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    @enforce_types
    def buy_from_fre_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        consume_market_order_fee_address: str,
        consume_market_order_fee_token: str,
        consume_market_order_fee_amount: int,
        exchange_contract: str,
        exchange_id: Any,
        max_base_token_amount: int,
        consume_market_swap_fee_amount: int,
        consume_market_swap_fee_address: str,
        transaction_parameters: dict,
    ) -> str:
        return self.contract.buyFromFreAndOrder(
            (
                ContractBase.to_checksum_address(consumer),
                service_index,
                (
                    checksum_addr(provider_fees["providerFeeAddress"]),
                    checksum_addr(provider_fees["providerFeeToken"]),
                    int(provider_fees["providerFeeAmount"]),
                    provider_fees["v"],
                    provider_fees["r"],
                    provider_fees["s"],
                    provider_fees["validUntil"],
                    provider_fees["providerData"],
                ),
                (
                    ContractBase.to_checksum_address(consume_market_order_fee_address),
                    ContractBase.to_checksum_address(consume_market_order_fee_token),
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
            transaction_parameters,
        )

    @enforce_types
    def buy_from_dispenser_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        consume_market_order_fee_address: str,
        consume_market_order_fee_token: str,
        consume_market_order_fee_amount: int,
        dispenser_address: str,
        transaction_parameters: dict,
    ) -> str:
        return self.contract.buyFromDispenserAndOrder(
            (
                ContractBase.to_checksum_address(consumer),
                service_index,
                (
                    checksum_addr(provider_fees["providerFeeAddress"]),
                    checksum_addr(provider_fees["providerFeeToken"]),
                    int(provider_fees["providerFeeAmount"]),
                    provider_fees["v"],
                    provider_fees["r"],
                    provider_fees["s"],
                    provider_fees["validUntil"],
                    provider_fees["providerData"],
                ),
                (
                    ContractBase.to_checksum_address(consume_market_order_fee_address),
                    ContractBase.to_checksum_address(consume_market_order_fee_token),
                    consume_market_order_fee_amount,
                ),
            ),
            ContractBase.to_checksum_address(dispenser_address),
            transaction_parameters,
        )

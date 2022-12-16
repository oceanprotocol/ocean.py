#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address


class DatatokenEnterprise(Datatoken):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    @enforce_types
    def buy_from_exchange_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        consume_market_order_fee_address: str,
        consume_market_order_fee_token: str,
        consume_market_order_fee_amount: int,
        exchange: Any,
        max_base_token_amount: int,
        consume_market_swap_fee_amount: int,
        consume_market_swap_fee_address: str,
        transaction_parameters: dict,
    ) -> str:
        fre_address = get_address_of_type(self.config_dict, "FixedPrice")

        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        if not isinstance(exchange, OneExchange):
            exchange = OneExchange(fre_address, exchange)

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
                ContractBase.to_checksum_address(exchange.address),
                exchange.exchange_id,
                max_base_token_amount,
                consume_market_swap_fee_amount,
                ContractBase.to_checksum_address(consume_market_swap_fee_address),
            ),
            transaction_parameters,
        )

    @enforce_types
    def dispense_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        transaction_parameters: dict,
        consume_market_order_fee_address: Optional[str] = None,
        consume_market_order_fee_token: Optional[str] = None,
        consume_market_order_fee_amount: Optional[int] = 0,
    ) -> str:
        dispenser_address = get_address_of_type(self.config_dict, "Dispenser")
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
                    ContractBase.to_checksum_address(
                        consume_market_order_fee_address or ZERO_ADDRESS
                    ),
                    ContractBase.to_checksum_address(
                        consume_market_order_fee_token or ZERO_ADDRESS
                    ),
                    consume_market_order_fee_amount,
                ),
            ),
            ContractBase.to_checksum_address(dispenser_address),
            transaction_parameters,
        )

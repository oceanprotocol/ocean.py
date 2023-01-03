#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Any, Union

from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken, TokenFeeInfo
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address


class DatatokenEnterprise(Datatoken):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    @enforce_types
    def buy_DT_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        exchange: Any,
        max_base_token_amount: Union[int, str],
        consume_market_swap_fee_amount: Union[int, str],
        consume_market_swap_fee_address: str,
        tx_dict: dict,
        consume_market_fees=None,
    ) -> str:
        fre_address = get_address_of_type(self.config_dict, "FixedPrice")

        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        if not isinstance(exchange, OneExchange):
            exchange = OneExchange(fre_address, exchange)

        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

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
                consume_market_fees.to_tuple(),
            ),
            (
                ContractBase.to_checksum_address(exchange.address),
                exchange.exchange_id,
                max_base_token_amount,
                consume_market_swap_fee_amount,
                ContractBase.to_checksum_address(consume_market_swap_fee_address),
            ),
            tx_dict,
        )

    @enforce_types
    def dispense_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        tx_dict: dict,
        consume_market_fees=None,
    ) -> str:
        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

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
                consume_market_fees.to_tuple(),
            ),
            ContractBase.to_checksum_address(dispenser_address),
            tx_dict,
        )

#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from typing import Union

from enforce_typing import enforce_types

from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC20Enterprise(ERC20Token):
    CONTRACT_NAME = "ERC20TemplateEnterprise"

    def buy_from_fre_and_order(
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
        exchange_contract: str,
        exchange_id: bytes,
        max_basetoken_amount: int,
        swap_market_fee: int,
        market_fee_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "buyFromFreAndOrder",
            (
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
                (
                    exchange_contract,
                    exchange_id,
                    max_basetoken_amount,
                    swap_market_fee,
                    market_fee_address,
                ),
            ),
            from_wallet,
        )

    def buy_from_dispenser_and_order(
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
        dispenser_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "buyFromDispenserAndOrder",
            (
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
                dispenser_address,
            ),
            from_wallet,
        )

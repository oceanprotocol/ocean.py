#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional, Union

import brownie
from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.models.fixed_rate_exchange import OneExchange
from ocean_lib.ocean.util import from_wei, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS


@enforce_types
class PredClass:
    def __init__(
        self,
        predval: bool,  # True = predict up, False = down
        stake: float,
        predictoor,
    ):
        self.predval: bool = predval
        self.stake: float = stake
        self.predictoor = predictoor
        self.paid: bool = False


@enforce_types
class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"

    def setup_exchange(self, tx_dict, rate: int):
        """
        Create an exchange with opinionated params:
         - Exchange's base token == self.stake_token
         - Exchange's owner is == this DT itself (!). Why: for payouts
        """
        self.exchange = self.create_exchange(
            tx_dict,
            rate,
            base_token_addr=self.stakeToken(),
        )

    def get_zero_provider_fee(self):
        return {
            "providerFeeAddress": ZERO_ADDRESS,
            "providerFeeToken": ZERO_ADDRESS,
            "providerFeeAmount": 0,
            "v": 0,
            "r": 0,
            "s": 0,
            "validUntil": 0,
            "providerData": 0,
        }

    def start_subscription_with_DT(self, tx_dict: dict):
        """ Start subscription if user has DT in his wallet """
        subscr_addr = tx_dict["from"].address
        assert not self.isValidSubscription(
            subscr_addr
        ), "this account has already started a subscription"
        self.approve_publish_market_order_fees(tx_dict)
        self.start_order(subscr_addr, 0, self.get_zero_provider_fee(), tx_dict)

    def start_subscription_with_buy_DT(self, exchange, tx_dict: dict):
        """ Start subscription by buying one DT and call order """
        subscr_addr = tx_dict["from"].address
        assert not self.is_valid_subscription(
            subscr_addr
        ), "this account has already started a subscription"
        self.approve_publish_market_order_fees(tx_dict)
        exchanges = self.get_exchanges()
        assert exchanges, "there are no fixed rate exchanges for this datatoken"
        exchange = exchanges[0]
        amt_needed = exchange.BT_needed(to_wei(1), 0)
        provider_fees = self.get_empty_provider_fee()

        return self.contract.buyFromFreAndOrder(
            (
                subscr_addr,
                0,
                (
                    provider_fees["providerFeeAddress"],
                    provider_fees["providerFeeToken"],
                    int(provider_fees["providerFeeAmount"]),
                    provider_fees["v"],
                    provider_fees["r"],
                    provider_fees["s"],
                    provider_fees["validUntil"],
                    provider_fees["providerData"],
                ),
                self.TokenFeeInfo(),
            ),
            (
                self.to_checksum_address(exchange.address),
                exchange.exchange_id,
                amt_needed,
                0,
                ZERO_ADDRESS,
            ),
            tx_dict,
        )

    def get_agg_predval(self, blocknum, tx_dict) -> float:
        (agg_predvals_numer, agg_predvals_denom) = self.getAggPredval(
            blocknum, tx_dict
        )
        return float(agg_predvals_numer / agg_predvals_denom)

    def _stake_token_bal(self) -> float:
        """How much e.g. OCEAN does this contract have?"""
        return from_wei(self.stake_token.balanceOf(self.treasurer))

    def _sell_1DT(self):
        amt_DT_wei = to_wei(1.0)
        amt_BT_wei = self.exchange.BT_received(amt_DT_wei, consume_market_fee=0)


@enforce_types
def _cur_blocknum() -> int:
    return brownie.network.chain[-1].number

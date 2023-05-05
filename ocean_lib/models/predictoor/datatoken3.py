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
    CONTRACT_NAME = "ERC20TemplatePredictoor"

    def setup_exchange(self, tx_dict, rate: int):
        """
        Create an exchange with opinionated params:
         - Exchange's base token == self.stake_token
         - Exchange's owner is == this DT itself (!). Why: for payouts
        """
        self.exchange = self.create_exchange(
            tx_dict,
            rate,
            base_token_addr=self.stake_token(),
        )

    

    def start_subscription_with_DT(self, tx_dict: dict):
        # Start subscription if user has DT in his wallet
        subscr_addr = tx_dict["from"].address
        assert (
            not self.is_valid_subscription(subscr_addr)
        ), "this account has already started a subscription"
        # TODO  - get publishMarketFee and approve tokens if needed
        # call startOrdrt

    def start_subscription_with_buy_DT(self, tx_dict: dict):
        # Start subscription by buying one DT and call order
        subscr_addr = tx_dict["from"].address
        assert (
            not self.is_valid_subscription(subscr_addr)
        ), "this account has already started a subscription"
        # TODO  - get publishMarketFee and approve tokens if needed
        # call buyFromFreAndOrder
        

    
    def _stake_token_bal(self) -> float:
        """How much e.g. OCEAN does this contract have?"""
        return from_wei(self.stake_token.balanceOf(self.treasurer))

    def _sell_1DT(self):
        amt_DT_wei = to_wei(1.0)
        amt_BT_wei = self.exchange.BT_received(amt_DT_wei, consume_market_fee=0)

    def buy_1DT(
        self,
        tx_dict: dict,
    ):
        """
        Buy 1 DT
        """

        consume_market_fee_addr = ZERO_ADDRESS
        consume_market_fee = 0
        exchanges = self.getFixedRates()
        exchange=exchanges[0]
        print(exchange)
        tx = self.contract.buyFromFre(
            (
            exchange[0],
            exchange[1],
            MAX_UINT256,
            consume_market_fee,
            consume_market_fee_addr
            ),
            tx_dict
        )
        return tx

@enforce_types
def _cur_blocknum() -> int:
    return brownie.network.chain[-1].number

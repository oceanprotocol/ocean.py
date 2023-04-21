#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1


class Prediction:
    def __init__(self, prediction, stake):
        self.prediction = prediction
        self.stake = stake
        self.score = 0
        self.paid = False


class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"  # switch to ERC20Template3 when ready

    def __init__(self, config_dict: dict, address: str) -> None:
        super().__init__(config_dict, address)
        self.subscribers = {}  # [address] = timestamp
        self.predictions = {}  # [predict_blocknum][address] = Prediction
        self.trueval = {}  # [blocknum] = trueval

        self.prediction_counter = {}  # [blocknum] = counter
        self.stake_counter = {}  # [blocknum] = counter

    # placeholders for now
    def submit_predval(self, token, prediction, stake, predict_blocknum, tx_dict):
        prediction = Prediction(prediction, stake)

        if predict_blocknum not in self.predictions:
            self.predictions[predict_blocknum] = {}
            self.prediction_counter[predict_blocknum] = 0
            self.stake_counter[predict_blocknum] = 0

        self.predictions[predict_blocknum][tx_dict["from"]] = prediction

        assert (token.transferFrom(
            tx_dict["from"], self.address, stake, {"from": self.address}
        ))

        self.prediction_counter[predict_blocknum] += 1
        self.stake_counter[predict_blocknum] += stake

    def get_agg_predval(self, stake, blocknum):
        pass

    def submit_trueval(self, blocknum, trueval, tx_dict):
        # assert sender == opf
        self.trueval[blocknum] = trueval

        # calc accuracy for each prediction
        inverse_sum = 0
        pred_inv = {}
        for addr in self.predictions[blocknum]:
            prediction = self.predictions[blocknum][addr]
            inverse_sum += 1 / prediction.prediction
            pred_inv[addr] = 1 / prediction.prediction

        for addr in self.predictions[blocknum]:
            prediction = self.predictions[blocknum][addr]
            prediction.score = pred_inv[addr] / inverse_sum

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp

    def get_agg_predval(self, blocknum):
        s = 0
        w = 0
        for addr in self.predictions[blocknum]:
            prediction = self.predictions[blocknum][addr]
            s += prediction.prediction * prediction.stake
            w += prediction.stake
        return s / w

    def get_payout(self, blocknum, OCEAN, predictoor_addr, tx_dict):
        assert (self.predictions[blocknum][predictoor_addr].paid == False)

        amt = self.predictions[blocknum][predictoor_addr].score * self.stake_counter[blocknum]
        if OCEAN.balanceOf(self.address) < amt:  # precision loss
            amt = OCEAN.balanceOf(self.address)
        assert (OCEAN.transfer(predictoor_addr, amt, {"from": self.address}))
        self.predictions[blocknum][predictoor_addr].paid = True

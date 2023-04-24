#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1


class Prediction:
    def __init__(self, prediction, stake, predictoor):
        self.predictoor = predictoor
        self.predval = prediction
        self.stake = stake
        self.score = 0
        self.paid = False


class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template"  # switch to ERC20Template3 when ready

    def __init__(self, config_dict: dict, address: str) -> None:
        super().__init__(config_dict, address)
        self.subscribers = {}  # [address] = timestamp
        self.predictions = {}  # [predict_blocknum][id] = Prediction
        self.trueval = {}  # [blocknum] = trueval

        self.prediction_counter = {}  # [blocknum] = counter
        self.stake_counter = {}  # [blocknum] = counter

        self.agg_predvals = {}  # [blocknum] = aggpredval
        self.sumdiff = {}  # [blocknum] = sumdiff
        self.sumdiff_counter = {}  # [blocknum] = counter

    # placeholders for now

    def submit_predval(self, token, prediction, stake, predict_blocknum, tx_dict):
        # assert blocks_ahead >= self._min_blocks_ahead

        prediction = Prediction(prediction, stake, predictoor=tx_dict["from"])

        if predict_blocknum not in self.predictions:
            self.predictions[predict_blocknum] = {}
            self.prediction_counter[predict_blocknum] = 0
            self.stake_counter[predict_blocknum] = 0
            self.sumdiff_counter[predict_blocknum] = 0
            self.sumdiff[predict_blocknum] = 0
            self.agg_predvals[predict_blocknum] = 0

        self.predictions[predict_blocknum][
            self.prediction_counter[predict_blocknum]
        ] = prediction

        assert token.transferFrom(
            tx_dict["from"], self.address, stake, {"from": self.address}
        )

        self.prediction_counter[predict_blocknum] += 1
        self.stake_counter[predict_blocknum] += stake
        self.agg_predvals[predict_blocknum] += int(
            prediction.predval * prediction.stake
        )  # need to normalize by sum of stakes

    def submit_trueval(self, blocknum, trueval, tx_dict):
        # assert sender == opf
        self.trueval[blocknum] = trueval

    def calc_sum_diff(self, blocknum, batchsize, tx_dict):
        assert self.sumdiff_counter[blocknum] < self.prediction_counter[blocknum]
        checked = 0
        for i in range(
            self.sumdiff_counter[blocknum], self.prediction_counter[blocknum]
        ):
            prediction = self.predictions[blocknum][i]
            if prediction.paid == False:
                if prediction.prediction > self.trueval[blocknum]:
                    self.sumdiff[blocknum] += (
                        prediction.prediction - self.trueval[blocknum]
                    ) * prediction.stake
                else:
                    self.sumdiff[blocknum] += (
                        self.trueval[blocknum] - prediction.prediction
                    ) * prediction.stake
                checked += 1
                self.sumdiff_counter[blocknum] += 1
            if checked == batchsize:
                break

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp

    def get_agg_predval(self, blocknum):
        return int(self.agg_predvals[blocknum])

    def get_payout(self, blocknum, OCEAN, id, tx_dict):
        assert self.predictions[blocknum][id].paid == False
        assert self.sumdiff_counter[blocknum] == self.prediction_counter[blocknum]
        prediction = self.predictions[blocknum][id]
        prediction.score = (
            prediction.prediction * 1e18 / self.sumdiff[blocknum]
        ) * prediction.stake

        amt = prediction.score * self.stake_counter[blocknum] / 1e18
        if OCEAN.balanceOf(self.address) < amt:  # precision loss
            amt = OCEAN.balanceOf(self.address)
        assert OCEAN.transfer(prediction.predictoor, amt, {"from": self.address})
        prediction.paid = True

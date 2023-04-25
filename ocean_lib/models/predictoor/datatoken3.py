#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.ocean.util import from_wei, to_wei


@enforce_types
class PredClass:
    def __init__(
        self,
        predval_trunc: int,  # e.g. "50020" here == "500.20" float
        stake_wei: int,
        predictoor,
    ):
        self.predval_trunc: int = predval_trunc
        self.stake_wei: int = stake_wei
        self.predictoor = predictoor

        self.score = 0
        self.paid: bool = False


@enforce_types
class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"

    def __init__(self, config_dict: dict, address: str) -> None:
        super().__init__(config_dict, address)
        self.subscribers = {}  # [address] = timestamp

        self.predobjs = {}  # [predict_blocknum][id] = predobj
        self.num_predobjs = {}  # [blocknum] = counter

        self.tot_stakes_wei = {}  # [blocknum] = stake_wei
        self.agg_predvals = {}  # [blocknum] = aggpredval

        self.truevals_trunc = {}  # [blocknum] = trueval_trunc

        self.sumdiffs = {}  # [blocknum] = sumdiff
        self.num_sumdiffs = {}  # [blocknum] = counter

    def submit_predval(
        self,
        stake_token: DatatokenBase,  # e.g. OCEAN
        predval_trunc: int,  # e.g. "50020" here == "500.20" float
        stake_wei: int,
        predict_blocknum: int,
        tx_dict: dict,
    ):
        # assert blocks_ahead >= self._min_blocks_ahead
        predictoor = tx_dict["from"]
        predobj = PredClass(predval_trunc, stake_wei, predictoor)

        if predict_blocknum not in self.predobjs:
            self.predobjs[predict_blocknum] = {}
            self.num_predobjs[predict_blocknum] = 0

            self.tot_stakes_wei[predict_blocknum] = 0
            self.agg_predvals[predict_blocknum] = 0

            self.sumdiffs[predict_blocknum] = 0
            self.num_sumdiffs[predict_blocknum] = 0

        predobj_i = self.num_predobjs[predict_blocknum]
        self.predobjs[predict_blocknum][predobj_i] = predobj

        bal_wei = stake_token.balanceOf(predictoor)
        assert (
            bal_wei >= stake_wei
        ), f"Predictoor has {from_wei(bal_wei)}, needed {from_wei(stake_wei)}"

        # DT contract transfers OCEAN stake from predictoor to itself
        # (.sol wouldn't have separate "treasurer" concept or the last arg)
        assert stake_token.transferFrom(
            tx_dict["from"], self.address, stake_wei, {"from": self.treasurer}
        )

        self.num_predobjs[predict_blocknum] += 1
        self.tot_stakes_wei[predict_blocknum] += stake_wei
        self.agg_predvals[predict_blocknum] += int(
            predobj.predval_trunc * predobj.stake_wei
        )

    def submit_trueval(
        self,
        blocknum: int,
        trueval_trunc: int,  # e.g. "44900" here == "449.00" float
        tx_dict: dict,
    ):
        # assert sender == opf
        self.truevals_trunc[blocknum] = trueval_trunc

    def calc_sum_diff(self, blocknum, max_num_loops, tx_dict):
        assert self.num_sumdiffs[blocknum] < self.num_predobjs[blocknum]
        num_loops_done = 0
        for predobj_i in range(
            self.num_sumdiffs[blocknum], self.num_predobjs[blocknum]
        ):
            predobj = self.predobjs[blocknum][predobj_i]
            if predobj.paid == False:
                predval_trunc = predobj.predval_trunc
                trueval_trunc = self.truevals_trunc[blocknum]
                diff = abs(predval_trunc - trueval_trunc)
                self.sumdiffs[blocknum] += diff * predobj.stake_wei
                num_loops_done += 1
                self.num_sumdiffs[blocknum] += 1
            if num_loops_done == max_num_loops:
                break

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp

    def get_agg_predval(self, blocknum):
        # this value will be encrypted
        return int(self.agg_predvals[blocknum])

    def get_payout(self, blocknum, stake_token, id, tx_dict):
        assert self.predobjs[blocknum][id].paid == False
        assert self.num_sumdiffs[blocknum] == self.num_predobjs[blocknum]
        predobj = self.predobjs[blocknum][id]
        predobj.score = 1 - predobj.stake_wei * (
            abs(predobj.predval_trunc - self.truevals_trunc[blocknum])
            / self.sumdiffs[blocknum]
        )
        amt_wei = predobj.score * self.tot_stakes_wei[blocknum]
        if stake_token.balanceOf(self.address) < amt_wei:  # precision loss
            amt_wei = stake_token.balanceOf(self.address)

        # DT contract transfers OCEAN winnings from itself to predictoor
        # (.sol wouldn't have separate "treasurer" concept or the last arg)
        assert stake_token.transfer(
            predobj.predictoor, amt_wei, {"from": self.treasurer}
        )

        predobj.paid = True

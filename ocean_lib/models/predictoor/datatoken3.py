#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.datatoken_base import DatatokenBase


@enforce_types
class PredClass:
    def __init__(
            self,
            predval_trunc: int, # e.g. "50020" here == "500.20" float
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
        self.truevals_trunc = {}  # [blocknum] = trueval_trunc

        self.num_predobjs = {}  # [blocknum] = counter
        self.tot_stakes_wei = {}  # [blocknum] = stake_wei
        self.agg_predvals = {}  # [blocknum] = aggpredval
        self.sumdiffs = {}  # [blocknum] = sumdiff
        self.num_sumdiffs = {}  # [blocknum] = counter

    # placeholders for now

    def submit_predval(
            self,
            stake_token: DatatokenBase, #e.g. OCEAN
            predval_trunc: int, # e.g. "50020" here == "500.20" float
            stake_wei: int,
            predict_blocknum: int,
            tx_dict: dict
    ):
        # assert blocks_ahead >= self._min_blocks_ahead

        predobj = PredClass(
            predval_trunc, stake_wei, predictoor=tx_dict["from"])

        if predict_blocknum not in self.predobjs:
            self.predobjs[predict_blocknum] = {}
            self.num_predobjs[predict_blocknum] = 0
            self.tot_stakes_wei[predict_blocknum] = 0
            self.num_sumdiffs[predict_blocknum] = 0
            self.sumdiffs[predict_blocknum] = 0
            self.agg_predvals[predict_blocknum] = 0

        self.predobjs[predict_blocknum][
            self.num_predobjs[predict_blocknum]
        ] = predobj

        assert stake_token.transferFrom(
            tx_dict["from"], self.address, stake_wei, {"from": self.address}
        )

        self.num_predobjs[predict_blocknum] += 1
        self.tot_stakes_wei[predict_blocknum] += stake_wei
        self.agg_predvals[predict_blocknum] += int(
            predobj.predval_trunc * predobj.stake_wei
        )

    def submit_trueval(
            self,
            blocknum: int,
            trueval_trunc: int, # e.g. "44900" here == "449.00" float
            tx_dict: dict,
    ):
        # assert sender == opf
        self.truevals_trunc[blocknum] = trueval_trunc

    def calc_sum_diff(self, blocknum, batchsize, tx_dict):
        assert self.num_sumdiffs[blocknum] < self.num_predobjs[blocknum]
        num_iterations = 0
        for i in range(
            self.num_sumdiffs[blocknum], self.num_predobjs[blocknum]
        ):
            predobj = self.predobjs[blocknum][i]
            if predobj.paid == False:
                diff = abs(predobj.predval_trunc - self.truevals_trunc[blocknum])
                self.sumdiffs[blocknum] += diff * predobj.stake_wei
                num_iterations += 1
                self.num_sumdiffs[blocknum] += 1
            if num_iterations == batchsize:
                break

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp

    def get_agg_predval(self, blocknum):
        # this value will be encrypted
        return int(self.agg_predvals[blocknum])

    def get_payout(self, blocknum, OCEAN, id, tx_dict):
        assert self.predobjs[blocknum][id].paid == False
        assert self.num_sumdiffs[blocknum] == self.num_predobjs[blocknum]
        predobj = self.predobjs[blocknum][id]
        predobj.score = 1 - predobj.stake_wei * (
            abs(predobj.predval_trunc - self.truevals_trunc[blocknum])
            / self.sumdiffs[blocknum]
        )
        amt = predobj.score * self.tot_stakes_wei[blocknum]
        if OCEAN.balanceOf(self.address) < amt:  # precision loss
            amt = OCEAN.balanceOf(self.address)
        assert OCEAN.transfer(predobj.predictoor, amt, {"from": self.address})
        predobj.paid = True

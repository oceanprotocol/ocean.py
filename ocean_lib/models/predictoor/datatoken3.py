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

        self.paid: bool = False

    def calc_swe(self, trueval_trunc: int) -> float:
        """@return - stake-weighted error (SWE)"""
        error_trunc = abs(self.predval_trunc - trueval_trunc)
        swe = error_trunc * self.stake_wei
        return swe


@enforce_types
class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"

    def __init__(self, config_dict: dict, address: str) -> None:
        super().__init__(config_dict, address)
        self.subscribers = {}  # [address] = timestamp

        self.predobjs = {}  # [predict_blocknum][id] = predobj
        self.len_predobjs = {}  # [blocknum] = counter

        self.agg_predvals_numerator_wei = {}  # [blocknum] = agg_predval_numer
        self.agg_predvals_denominator_wei = {}  # [blocknum] = agg_predval_denom

        self.truevals_trunc = {}  # [blocknum] = trueval_trunc

        self.agg_SWEs = {}  # [blocknum] = agg_stake_weighted_errors
        self.len_agg_SWEs = {}  # [blocknum] = counter

    def submit_predval(
        self,
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
            self.len_predobjs[predict_blocknum] = 0

            self.agg_predvals_numerator_wei[predict_blocknum] = 0
            self.agg_predvals_denominator_wei[predict_blocknum] = 0

            self.agg_SWEs[predict_blocknum] = 0
            self.len_agg_SWEs[predict_blocknum] = 0

        predobj_i = self.len_predobjs[predict_blocknum]
        self.predobjs[predict_blocknum][predobj_i] = predobj

        bal_wei = self.stake_token.balanceOf(predictoor)
        assert (
            bal_wei >= stake_wei
        ), f"Predictoor has {from_wei(bal_wei)}, needed {from_wei(stake_wei)}"

        # DT contract transfers OCEAN stake from predictoor to itself
        # py version, with "treasurer"  workaround:
        assert self.stake_token.transferFrom(
            predictoor, self.treasurer, stake_wei, {"from": self.treasurer}
        )
        # sol version would look something like this:
        # assert self.stake_token.transferFrom(predictoor, self.address, stake_wei)

        self.len_predobjs[predict_blocknum] += 1
        self.agg_predvals_numerator_wei[predict_blocknum] += int(
            predobj.predval_trunc * predobj.stake_wei
        )
        self.agg_predvals_denominator_wei[predict_blocknum] += stake_wei

    def submit_trueval(
        self,
        blocknum: int,
        trueval_trunc: int,  # e.g. "44900" here == "449.00" float
        tx_dict: dict,
    ):
        # assert sender == opf
        self.truevals_trunc[blocknum] = trueval_trunc

    def start_subscription(self, tx_dict):
        if tx_dict["from"] not in self.subscribers:
            self.subscribers[tx_dict["from"]] = 100  # mock timestamp

    def get_agg_predval_numerator(self, blocknum):
        # this value will be encrypted
        return int(self.agg_predvals_numerator_wei[blocknum])

    def get_agg_predval_denominator(self, blocknum):
        # this value will be encrypted
        return int(self.agg_predvals_denominator_wei[blocknum])

    def update_error_calcs(self, blocknum, max_num_loops, tx_dict):
        assert (
            self.len_agg_SWEs[blocknum] < self.len_predobjs[blocknum]
        ), "don't need to call this, there's nothing left to calc"
        num_predobjs_done = self.len_agg_SWEs[blocknum]
        tot_num_predobjs = self.len_predobjs[blocknum]
        num_loops_done = 0
        for predobj_i in range(num_predobjs_done, tot_num_predobjs):
            predobj = self.predobjs[blocknum][predobj_i]
            if not predobj.paid:
                swe = predobj.calc_swe(self.truevals_trunc[blocknum])
                self.agg_SWEs[blocknum] += swe
                num_loops_done += 1
                self.len_agg_SWEs[blocknum] += 1
            if num_loops_done == max_num_loops:
                break

    def get_payout(self, blocknum, id, tx_dict):
        assert self.predobjs[blocknum][id].paid == False
        assert self.len_agg_SWEs[blocknum] == self.len_predobjs[blocknum]

        predobj = self.predobjs[blocknum][id]

        swe = predobj.calc_swe(self.truevals_trunc[blocknum])
        tot_swe = self.agg_SWEs[blocknum]

        perc_payout = 1.0 - swe / tot_swe  # % that this predictoor gets
        tot_stake_wei = self.agg_predvals_denominator_wei[blocknum]
        payout_wei = perc_payout * tot_stake_wei
        if self.stake_token.balanceOf(self.address) < payout_wei:  # precision loss
            payout_wei = self.stake_token.balanceOf(self.address)

        # DT contract transfers OCEAN winnings from itself to predictoor
        # py version, with "treasurer"  workaround:
        assert self.stake_token.transfer(
            predobj.predictoor, payout_wei, {"from": self.treasurer}
        )
        # sol version would look something like this:
        # assert self.stake_token.transfer(predobj.predictoor, payout_wei)

        predobj.paid = True

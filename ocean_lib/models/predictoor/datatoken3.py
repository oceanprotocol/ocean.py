#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

import brownie
from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.models.fixed_rate_exchange import OneExchange
from ocean_lib.ocean.util import from_wei, to_wei


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

        self.swe = None #swe = stake-weighted error
        self.paid: bool = False

    def set_swe(self, trueval: bool) -> float:
        """@return - stake-weighted error (SWE)"""
        # SWE = abs(trueval - predicted) * stake
        # Implementation is simple because of booleans
        assert self.swe is None, "already set swe"
        if self.predval == trueval:
            self.swe = 0.0
        self.swe = self.stake


@enforce_types
class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3"

    def do_setup(
            self,
            s_per_block: int, # seconds per block
            s_per_epoch: int, # seconds per epoch
            s_per_subscription: int, # seconds per subscription
            min_predns_for_payout: int, # min # pr'dns by a pr'oor for payout
            stake_token: DatatokenBase, # e.g. OCEAN
    ):
        """
        Set DT-specific attributes.(Eventually, ERC20Template3.sol will hold)
        """
        # State variables
        self.startblock_per_subscriber = {}  # [subscriber_address] : blocknum
        
        self.predobjs = {}  # [predict_blocknum][predictoor_addr] : predobj
        self.agg_predvals_numer = {}  # [blocknum] : agg_predval_numerator
        self.agg_predvals_denom = {}  # [blocknum] : agg_predval_denominator
        
        self.truevals = {}  # [blocknum] : trueval -- float in [0.0, 1.0]
        
        self.SWEs = {}  # [blocknum][predictoor_addr] : stake_weighted_errors

        # Calc & set epoch parameters
        # - Specify epochs in terms of block numbers. Ie give "slots" to epochs.
        # - When one epoch ends, the next begins
        assert s_per_subscription % s_per_block == 0, "must cleanly divide"
        assert s_per_epoch % s_per_block == 0, "must cleanly divide"
        
        self.blocks_per_epoch = s_per_epoch / s_per_block
        self.blocks_per_subscription = s_per_subscription / s_per_block

        # Set other attributes
        self.min_predns_for_payout = min_predns_for_payout
        self.stake_token = stake_token # for staking *and* payment

    def epoch(self, blocknum: int) -> int:
        return int(blocknum // self.blocks_per_epoch)
    
    def cur_epoch(self) -> int:
        return int(_cur_blocknum() // self.blocks_per_epoch)
        
    def rail_blocknum_to_slot(self, blocknum):
        return int(blocknum // self.blocks_per_epoch * self.blocks_per_epoch)

    def blocknum_is_on_a_slot(self, blocknum) -> bool:
        # a slot == beginning/end of an epoch
        return blocknum == self.rail_blocknum_to_slot(blocknum)

    def setup_exchange(self, tx_dict, rate: int):
        """
        Create an exchange with opinionated params:
         - Exchange's base token == self.stake_token
         - Exchange's owner is == this DT itself (!). Why: for payouts
        """
        self.exchange = self.create_exchange(
            tx_dict,
            rate,
            base_token_addr=self.stake_token.address,
            #when solidity, change to: owner_addr=self
            owner_addr=self.treasurer.address,
        )

    def soonest_block_to_predict(self) -> int:
        """What's the next block that a predictoor could predict at,
        without breaking the rules about predicting too early?"""
        cur_blocknum = _cur_blocknum()
        slotted_blocknum = self.rail_blocknum_to_slot(cur_blocknum)
        if slotted_blocknum == cur_blocknum: # currently at a slot
            blocknum = slotted_blocknum + self.blocks_per_epoch
        else:
            blocknum = slotted_blocknum + 2 * self.blocks_per_epoch
        assert self.blocknum_is_on_a_slot(blocknum)
        return blocknum

    def submitted_predval(self, blocknum:int, predictoor_addr:str) -> bool:
        """Did this predictoor submit a predval for this blocknum?"""
        assert self.blocknum_is_on_a_slot(blocknum)
        if blocknum not in self.predobjs:
            return False
        return predictoor_addr in self.predobjs[blocknum]
        
    def submit_predval(
        self,
        predval: bool, # True = predict up, False = down
        stake: float,
        blocknum: int, # block number to predict at
        tx_dict: dict,
    ):
        """Predictoor submits prediction"""
        assert self.blocknum_is_on_a_slot(blocknum)
        assert blocknum >= self.soonest_block_to_predict()
        
        predictoor = tx_dict["from"]
        predobj = PredClass(predval, stake, predictoor)

        if blocknum not in self.predobjs:
            self.predobjs[blocknum] = {}
            self.agg_predvals_numer[blocknum] = 0.0
            self.agg_predvals_denom[blocknum] = 0.0

        self.predobjs[blocknum][predictoor.address] = predobj

        # aa = amt allowed, ie what treasurer can spend on behalf of predictoor
        aa = from_wei(self.stake_token.allowance(predictoor, self.treasurer))
        assert aa >= stake

        # DT contract transfers OCEAN stake from predictoor to itself
        # py version, with "treasurer"  workaround:
        assert self.stake_token.transferFrom(
            predictoor, self.treasurer, to_wei(stake), {"from": self.treasurer}
        )
        # sol version would look something like this:
        # assert self.stake_token.transferFrom(predictoor, self.address, stake_wei)

        self.agg_predvals_numer[blocknum] += predobj.stake * predobj.predval
        self.agg_predvals_denom[blocknum] += stake

    def submit_trueval(
        self,
        trueval: bool, # True = value went up, False = value went down
        blocknum: int, # block number for this submitted value
        tx_dict: dict,
    ):
        assert self.blocknum_is_on_a_slot(blocknum)
        # assert sender == opf
        # FIXME: in sol, this should be an oracle
        self.truevals[blocknum] = trueval

    def start_subscription(self, tx_dict: dict):
        # A bit like pay_for_access_service, but super simple! No need for DDO.
        subscr_addr = tx_dict["from"].address
        assert subscr_addr not in self.startblock_per_subscriber, \
            "this account has already started a subscription"
        self.startblock_per_subscriber[subscr_addr] = _cur_blocknum()

    def get_agg_predval(self, blocknum: int) -> float:
        """Returns a value between 0.0 and 1.0. 
        = 0.5: expect no change in value
        > 0.5: expect value to go UP. Closer to 1.0 = more confident
        < 0.5: expect value to go down. Closer to 0.0 = more confident
        """
        assert self.blocknum_is_on_a_slot(blocknum)
        
        # this value will be encrypted
        numer = self.agg_predvals_numer[blocknum]
        denom = self.agg_predvals_denom[blocknum]

        return numer / denom

    def update_error_calcs(self, blocknum: int, tx_dict: dict):
        assert self.blocknum_is_on_a_slot(blocknum)
        trueval = self.truevals[blocknum]
        for predobj in self.predobjs[blocknum].values():
            if predobj.swe is None:
                predobj.set_swe(trueval)

    def update_payouts(self, blocknum: int, predictoor_addr: str, tx_dict: dict):
        assert self.blocknum_is_on_a_slot(blocknum)
        
        predobj = self.predobjs[blocknum][predictoor_addr]
        assert not predobj.paid, "already got paid"
        
        swes = [other_predobj.swe
                for other_predobj in self.predobjs[blocknum].values()]
        assert None not in swes, "must calc all SWEs first"

        # calculate predictoor's score. In range [0.0, 1.0]. 1.0 is best.
        score01 = 1.0 - predobj.swe / sum(swes)

        # the DT gets revenue comes from two places:
        # (1) subscription, ie $ to exchange for DTs
        # (2) stake reallocation
        tot_rev_subscr = self._subscription_revenue_at_block(blocknum)
        tot_rev_stake = self.agg_predvals_denom[blocknum]

        # the DT's revenue gets paid out to subscribers, pro-rata on score
        # (FIXME: have a cut to OPC/OPF)
        payout = score01 * (tot_rev_subscr + tot_rev_stake)

        # top up DT's balance if needed by selling DTs into the exchange
        # FIXME: make this cleaner, without a loop
        while self._stake_token_bal() < payout:
            self.exchange.sell_DT(to_wei(1.0), {"from": self.treasurer})

        # now do payout to the predictoor
        # - use "increaseAllowance()", not "approve()", to build on previous amts
        self.stake_token.increaseAllowance(
            predobj.predictoor, to_wei(payout), {"from": self.treasurer})
        predobj.paid = True

        # Note: we don't need to delete old predobjs, since Solidity
        # can handle the storage

    def _stake_token_bal(self) -> float:
        """How much e.g. OCEAN does this contract have?"""
        return from_wei(self.stake_token.balanceOf(self.treasurer))

    def _sell_1DT(self):
        amt_DT_wei = to_wei(1.0)
        amt_BT_wei = self.exchange.BT_received(amt_DT_wei, consume_market_fee=0)

    def _subscription_revenue_at_block(self, blocknum) -> float:
        assert self.blocknum_is_on_a_slot(blocknum)

        # revenue per subscriber, at this block
        price = from_wei(self.exchange.details.fixed_rate)
        rev_per_subscr = price / self.blocks_per_subscription

        # total number of subscribers at this block
        n_subscr = 0
        for startblock in self.startblock_per_subscriber.values():
            endblock = startblock + self.blocks_per_subscription
            n_subscr += (startblock <= blocknum < endblock)

        return rev_per_subscr * n_subscr

@enforce_types
def _cur_blocknum() -> int:
    return brownie.network.chain[-1].number

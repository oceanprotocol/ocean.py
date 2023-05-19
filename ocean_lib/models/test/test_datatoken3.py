"""Prototype 3. Uses OCEAN staking, and DTs."""
import json
import os
import random
import sys

import brownie
from brownie.network import accounts as br_accounts
from enforce_typing import enforce_types
import pytest
from pytest import approx

from ocean_lib.example_config import get_config_dict
from ocean_lib.models.datatoken3 import Datatoken3
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.util import from_wei, to_wei
from ocean_lib.web3_internal.constants import ZERO_ADDRESS, MAX_UINT256
from ocean_lib.web3_internal.utils import connect_to_network


# must be the same file as generated by deploy.py
ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"

chain = brownie.network.chain

S_PER_MIN = 60
S_PER_HOUR = 60 * 60


@enforce_types
def test_main():
    # ======================================================================
    # SETUP
    config, ocean, OCEAN, accts = _setup()
    [deployer, opf, predictoor0, predictoor1, trader, rando, DT_treasurer] = accts
    predictoors = [predictoor0, predictoor1]

    # convenience functions
    OCEAN_bal = ConvClass(OCEAN).fromWei_balanceOf
    OCEAN_approved = ConvClass(OCEAN).fromWei_approved

    # ======================================================================
    # PARAMETERS
    s_per_block = 2  # depends on the chain
    s_per_epoch = 5 * S_PER_MIN
    s_per_subscription = 24 * S_PER_HOUR
    min_predns_for_payout = 3  # ideally, 100+
    stake_token = OCEAN
    stakes = [2.0, 1.0]  # Stake per predictoor. In OCEAN

    n_DTs = 100.0  # num DTs for sale
    DT_price = 10.0  # denominated in OCEAN

    max_n_predns = min_predns_for_payout  # stop loop after this many predn's

    x = ocean.data_nft_factory.getCurrentTemplateCount()

    # ======================================================================
    # DEPLOY DATATOKEN & EXCHANGE CONTRACT
    data_nft = ocean.data_nft_factory.create({"from": opf}, "DN", "DN")

    # since data_nft.create_datatoken does not allow us to send all the arrays, we have to do it manually
    # DT = data_nft.create_datatoken({"from": opf}, "DT", "DT", template_index=3)
    initial_list = data_nft.getTokensList()
    data_nft.createERC20(
        3,
        ["ETH-USDT", "ETH-USDT"],
        [opf.address, opf.address, opf.address, OCEAN.address, OCEAN.address],
        [MAX_UINT256, 0, s_per_block, s_per_epoch, s_per_subscription, 30],
        [],
        {"from": opf},
    )
    new_elements = [
        item for item in data_nft.getTokensList() if item not in initial_list
    ]
    assert len(new_elements) == 1, "new datatoken has no address"
    DT = DatatokenBase.get_typed(config, new_elements[0])

    # Mixed sol+py can't have DT to hold OCEAN, so have a different account
    # - When we convert to Solidity, change to: DT_treasurer = DT
    DT.treasurer = DT_treasurer

    # post DTs for sale
    DT.setup_exchange({"from": opf}, to_wei(DT_price))
    DT.approve(DT.exchange.address, to_wei(n_DTs), {"from": opf})

    # ======================================================================
    # TRADER BUYS SUBSCRIPTION TO AGG PREDVALS (do every 24h)

    # trader buys 1 DT with OCEAN
    exchange = DT.get_exchanges()[0]
    OCEAN_needed = from_wei(exchange.BT_needed(to_wei(1), consume_market_fee=0))
    OCEAN.approve(exchange.address, to_wei(OCEAN_needed), {"from": trader})

    consume_market_fee_addr = ZERO_ADDRESS
    consume_market_fee = 0
    tx = exchange.buy_DT(
        datatoken_amt=to_wei(1),
        consume_market_fee_addr=consume_market_fee_addr,
        consume_market_fee=consume_market_fee,
        tx_dict={"from": trader},
    )
    # trader starts subscription. Good for 24h.
    DT.approve(DT.address, to_wei(1), {"from": trader})
    DT.start_subscription_with_DT({"from": trader})  # good for next 24h

    assert DT.isValidSubscription(trader.address) == True
    # ======================================================================
    # ======================================================================
    # LOOP across epochs
    for stake, p in zip(stakes, predictoors):
        amt_approve = stake * max_n_predns
        OCEAN.approve(DT.address, to_wei(amt_approve), {"from": p})

    blocks_seen_by_trader = set()
    n_predns = {0: 0, 1: 0}  # [predictoor_i] : n_predns
    blocks_predicted = set()
    blocks_with_truevals = set()
    while True:
        actions_s = ""

        # PREDICTOORS STAKE & SUBMIT PREDVALS (do every 5min)
        for p_i, p in enumerate([predictoor0, predictoor1]):
            if n_predns[p_i] >= max_n_predns:
                continue

            predict_blocknum = DT.soonestBlockToPredict(cur_blocknum() + 1)
            if DT.submittedPredval(predict_blocknum, p.address):
                continue
            predval = random.choice([True, False])
            DT.submitPredval(predval, stakes[p_i], predict_blocknum, {"from": p})
            aa = OCEAN_approved(p, DT_treasurer)
            n_predns[p_i] += 1
            actions_s += (
                f"Predictoor{p_i+1} "
                + f" submitted pred'n #{n_predns[p_i]}"
                + f" at block B={predict_blocknum}, epoch E={DT.curEpoch()}."
                + f" Now, OCEAN approved={aa:.1f}\n"
            )
            blocks_predicted.add(predict_blocknum)
        print(blocks_predicted)
        # TRADER GETS AGG PREDVAL (do every 5min)
        blocks_not_seen = blocks_predicted - blocks_seen_by_trader
        for predict_blocknum in blocks_not_seen:
            prediction = DT.get_agg_predval(predict_blocknum, {"from": trader})
            assert 0.0 <= prediction <= 1.0
            blocks_seen_by_trader.add(predict_blocknum)
            actions_s += (
                f"Trader got agg_predval {prediction}"
                + f"at block B={int(predict_blocknum)}\n"
            )

        # OWNER SUBMITS TRUE VALUE. This will update predictoors' claimable amts
        for predict_blocknum in blocks_predicted:
            if DT.epochStatus(predict_blocknum):  # already set
                blocks_with_truevals.add(predict_blocknum)
                continue
            if cur_blocknum() < predict_blocknum:  # not enough time passed
                continue
            trueval = random.choice([True, False])
            DT.submitTrueVal(predict_blocknum, trueval,0,False, {"from": opf})
            blocks_with_truevals.add(predict_blocknum)
            chain.mine(1)  # forced this, because prev step isn't on chain
            actions_s += "OPF submitted a trueval\n"

        # MAYBE MINE. LOG OUTPUT
        block_s = f"[B={cur_blocknum()}, E={DT.curEpoch()}]"
        if actions_s == "":  # nothing happened, so move forward by a block
            chain.mine(1)
            s = "."
            if cur_blocknum() % 50 == 0:
                s = block_s
            print(s, end="")
            sys.stdout.flush()  # needed to make s show up immediately
        else:
            print()
            print(f"=" * 30 + "\n" + block_s + "\n" + actions_s)

        # STOP?
        if min(n_predns.values()) >= max_n_predns and (
            blocks_with_truevals == blocks_predicted
        ):
            print("STOP loop. Hit target # predictions, and have truevals.")
            break

    # ======================================================================
    # PREDICTOORS & OPF COLLECT SALES REVENUE
    initbalDT = OCEAN_bal(DT_treasurer)
    initbal0, initbal1 = OCEAN_bal(predictoor0), OCEAN_bal(predictoor1)

    # Any rando can call update_payouts(). Will update allowances

    # TODO.   This now fails because predictoors are pushing random values, and so does OPF.
    # Chances to hit a match are slim

    # DT.payout(predict_blocknum, predictoor0.address, {"from": rando})
    # DT.payout(predict_blocknum, predictoor1.address, {"from": rando})

    # balDT = OCEAN_bal(DT_treasurer)
    # bal0, bal1 = OCEAN_bal(predictoor0), OCEAN_bal(predictoor1)
    # earned0, earned1 = (bal0 - initbal0), (bal1 - initbal1)
    # earned = earned0 + earned1

    # assert balDT == initbalDT - earned
    # assert bal0 > initbal0
    # assert bal1 > initbal1
    # End of TODO


def _setup():
    # ======================================================================
    # SETUP SYSTEM
    connect_to_network("development")

    # create base accounts
    deployer = br_accounts.add(os.getenv("FACTORY_DEPLOYER_PRIVATE_KEY"))
    opf = br_accounts.add(os.getenv("TEST_PRIVATE_KEY1"))

    # set ocean object
    address_file = os.path.expanduser(ADDRESS_FILE)
    print(f"Load contracts from address_file: {address_file}")
    config = get_config_dict("development")
    config["ADDRESS_FILE"] = address_file
    ocean = Ocean(config)

    # DEPLOYER mints 20K OCEAN, and sends 2K OCEAN to TEST_PRIVATE_KEY1 & 2
    mint_fake_OCEAN(config)

    # convenience objects
    OCEAN = ocean.OCEAN_token
    OCEAN_bal = ConvClass(OCEAN).fromWei_balanceOf

    # ======================================================================
    # SETUP USER ACCOUNTS
    # Ensure that users have OCEAN and ETH as needed
    # -Note: Barge minted fake OCEAN and gave it to TEST_PRIVATE_KEY{1,2}
    # -Note: we don't _need_ to have private keys 3-6. But doing it means
    #  we can give them ETH on launch rather than here, which is faster

    def _acct(key_i: int):
        return br_accounts.add(os.getenv(f"TEST_PRIVATE_KEY{key_i}"))

    predictoor0, predictoor1, trader, rando, DT_treasurer = (
        _acct(2),
        _acct(3),
        _acct(4),
        _acct(5),
        _acct(6),
    )

    accts = [deployer, opf, predictoor0, predictoor1, trader, rando, DT_treasurer]
    accts_needing_ETH = [opf, predictoor0, predictoor1, trader, rando, DT_treasurer]
    accts_needing_OCEAN = [opf, predictoor0, predictoor1, trader]

    print("\nBalances before moving funds:")
    for i, acct in enumerate(accts):
        print(f"acct {i}: {ETH_bal(acct)} ETH, {OCEAN_bal(acct)} OCEAN")

    print("\nMove ETH...")
    for acct in accts_needing_ETH:
        if ETH_bal(acct) == 0:
            deployer.transfer(acct, to_wei(1.0))

    print("\nMove OCEAN...")
    for acct in accts_needing_OCEAN:
        if OCEAN_bal(acct) <= 25.0:
            OCEAN.transfer(acct, to_wei(250.0), {"from": deployer})

    print("\nBalances after moving funds:")
    for i, acct in enumerate(accts):
        print(f"acct {i}: {ETH_bal(acct)} ETH, {OCEAN_bal(acct)} OCEAN")

    return config, ocean, OCEAN, accts


@enforce_types
class ConvClass:
    def __init__(self, token):
        self.token = token

    def fromWei_balanceOf(self, obj) -> float:
        return from_wei(self.token.balanceOf(obj.address))

    def fromWei_approved(self, obj1, obj2) -> float:
        return from_wei(self.token.allowance(obj1.address, obj2.address))


@enforce_types
def ETH_bal(acct) -> int:
    return from_wei(acct.balance())


@enforce_types
def cur_blocknum() -> int:
    return chain[-1].number

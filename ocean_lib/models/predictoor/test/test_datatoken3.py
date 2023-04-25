"""Prototype 3. Uses OCEAN staking, and DTs."""
import json
import os

import brownie
from brownie.network import accounts as br_accounts
from enforce_typing import enforce_types
import pytest
from pytest import approx

from ocean_lib.example_config import get_config_dict
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.util import from_wei, to_wei

# must be the same file as generated by deploy.py
ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"

chain = brownie.network.chain


@pytest.mark.unit
def test_main_py():
    _test_main(use_py=True)


@pytest.mark.unit
@pytest.mark.skip(reason="turn this on once .sol version is built")
def test_main_sol():
    _test_main(use_py=False)


@enforce_types
def _test_main(use_py):

    # ======
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
    ocean = Ocean(config, "no_provider")

    # DEPLOYER mints 20K OCEAN, and sends 2K OCEAN to TEST_PRIVATE_KEY1 & 2
    mint_fake_OCEAN(config)

    # convenience objects
    OCEAN = ocean.OCEAN_token

    # convenience functions
    c = ConvClass(OCEAN)
    OCEAN_bal = c.fromWei_balanceOf
    OCEAN_approved = c.fromWei_approved

    def ETH_bal(acct):
        return from_wei(acct.balance())

    # ======================================================================
    # SETUP USER ACCOUNTS
    # Ensure that users have OCEAN and ETH as needed
    # -Note: Barge minted fake OCEAN and gave it to TEST_PRIVATE_KEY{1,2}
    # -Note: we don't _need_ to have private keys 3-6. But doing it means
    #  we can give them ETH on launch rather than here, which is faster

    def _acct(key_i: int):
        return br_accounts.add(os.getenv(f"TEST_PRIVATE_KEY{key_i}"))
    predictoor1, predictoor2, trader, rando, treasurer = \
        _acct(2), _acct(3), _acct(4), _acct(5), _acct(6)
    
    accts = [deployer, opf, predictoor1, predictoor2, trader, rando, treasurer]
    accts_needing_ETH = [opf, predictoor1, predictoor2, trader, rando,treasurer]
    accts_needing_OCEAN = [opf, predictoor1, predictoor2, trader]

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
            OCEAN.transfer(acct, to_wei(25.0), {"from": deployer})

    print("\nBalances after moving funds:")
    for i, acct in enumerate(accts):
        print(f"acct {i}: {ETH_bal(acct)} ETH, {OCEAN_bal(acct)} OCEAN")

    predictoors = [predictoor1, predictoor2]

    # ======================================================================
    # DEPLOY DATATOKEN & EXCHANGE CONTRACT

    min_blocks_ahead = 20  # Pred'ns must be >= this # blocks ahead
    min_predns_for_payout = 100  # Pred'oor needs >= this # predn's to get paid
    num_blocks_subscription = 86400 / 10  # 1 day

    # can reuse existing DNFT template
    data_nft = ocean.data_nft_factory.create(
        {"from": opf},
        "Data NFT 1",
        "DNFT1",  # and any other DataNFTArguments
    )

    # new DT template with Predictoor functionality

    # params
    n_DTs = 100.0
    DT_price = 10.0  # denominated in OCEAN

    DT = data_nft.create_datatoken(
        {"from": opf},
        name="DT",
        symbol="DT",
        template_index=3,
        min_blocks_ahead=min_blocks_ahead,
        min_predns_for_payout=min_predns_for_payout,
        num_blocks_subscription=num_blocks_subscription,
        # and any other DatatokenArguments
    )
    assert DT.getId() == 3
    DT = DT.get_typed(config, DT.address)
    if use_py:  # py needs a treasurer, sol doesn't
        DT.treasurer = treasurer

    # post 100 DTs for sale
    DT.mint(opf, to_wei(n_DTs), {"from": opf})
    exchange = DT.create_exchange({"from": opf}, to_wei(DT_price), OCEAN.address)
    DT.approve(exchange.address, to_wei(n_DTs), {"from": opf})

    # ======================================================================
    # TRADER BUYS SUBSCRIPTION TO AGG PREDVALS (do every 24h)

    # trader buys 1 DT with OCEAN
    OCEAN_needed = from_wei(exchange.BT_needed(to_wei(1), consume_market_fee=0))
    assert OCEAN_bal(trader) >= OCEAN_needed, "must fund more OCEAN to trader"

    OCEAN.approve(exchange.address, to_wei(OCEAN_needed), {"from": trader})
    exchange.buy_DT(to_wei(1), {"from": trader})  # spends OCEAN

    # trader starts subscription. Good for 24h.
    # -"start_subscription" is like pay_for_access_service, but w/o DDO
    DT.approve(DT.address, to_wei(1), {"from": trader})
    DT.start_subscription({"from": trader})  # good for next 24h (or 1h, 7d, ..)

    # ======================================================================
    # PREDICTOORS STAKE & SUBMIT PREDVALS (do every 5min)
    stake1 = 20.0  # in OCEAN
    stake2 = 10.0  # ""
    predval1_trunc = 20000  # "20000" here == "200.00" float
    predval2_trunc = 50020  # "50020" here == "500.20" float
    predict_blocknum = 100

    assert OCEAN_bal(predictoor1) >= stake1, "must fund more OCEAN to prdoor1"
    assert OCEAN_bal(predictoor2) >= stake2, "must fund more OCEAN to prdoor2"

    if use_py:
        OCEAN.approve(DT.treasurer, to_wei(stake1), {"from": predictoor1})
        OCEAN.approve(DT.treasurer, to_wei(stake2), {"from": predictoor2})
        assert OCEAN_approved(predictoor1, DT.treasurer) == stake1
        assert OCEAN_approved(predictoor2, DT.treasurer) == stake2
    else:
        OCEAN.approve(DT, to_wei(stake1), {"from": predictoor1})
        OCEAN.approve(DT, to_wei(stake2), {"from": predictoor2})
        assert OCEAN_approved(predictoor1, DT) == stake1
        assert OCEAN_approved(predictoor2, DT) == stake2

    initbal1 = OCEAN_bal(predictoor1)
    initbal2 = OCEAN_bal(predictoor2)

    DT.submit_predval(
        OCEAN, predval1_trunc, to_wei(stake1), predict_blocknum, {"from": predictoor1}
    )
    DT.submit_predval(
        OCEAN, predval2_trunc, to_wei(stake2), predict_blocknum, {"from": predictoor2}
    )

    # test
    if use_py:
        assert OCEAN_bal(DT.treasurer) == (stake1 + stake2)
    else:
        assert OCEAN_bal(DT) == (stake1 + stake2)
    assert OCEAN_bal(predictoor1) == approx(initbal1 - stake1)  # just staked
    assert OCEAN_bal(predictoor2) == approx(initbal2 - stake2)  # ""
    assert OCEAN_approved(predictoor1, DT) == 0.0  # just used up
    assert OCEAN_approved(predictoor2, DT) == 0.0  # ""

    # ======================================================================
    # TRADER GETS AGG PREDVAL (do every 5min)

    # trader gets prediction itself
    # -a tx isn't needed, therefore Solidity can return a value directly
    # -"get_agg_predval" is like ocean.assets.download_asset //
    #  asset_downloader.download_asset_files() except there's no downloading,
    #  rather it simply gives the agg_predval. (To generalize: reveals secret)
    agg_predval_trunc = DT.get_agg_predval(predict_blocknum)
    assert agg_predval_trunc == approx(
        to_wei(predval1_trunc * stake1 + predval2_trunc * stake2)
    )  # need to normalize by sum of stakes

    # ======================================================================
    # TIME PASSES - enough such that predict_blocknum has passed
    chain.mine(min_blocks_ahead + 10)  # pass enough time (blocks) so that  pass

    # ======================================================================
    # OWNER SUBMITS TRUE VALUE. This will update predictoors' claimable amts
    trueval_trunc = 44900  # "44900" here == "449.00" float
    DT.submit_trueval(predict_blocknum, trueval_trunc, {"from": opf})

    # anyone can call calc_sum_diff()
    DT.calc_sum_diff(predict_blocknum, 1000, {"from": opf})

    # ======================================================================
    # TIME PASSES - enough for predictoors to get claims

    # FIXME - we'll need to do 'min_predns_for_payout' loops through this
    #   step and and several prev steps, for predictoors to actually get paid
    print(int(1.2 * min_blocks_ahead * min_predns_for_payout))
    # chain.mine(int(1.2 * min_blocks_ahead * min_predns_for_payout))

    # ======================================================================
    # PREDICTOORS & OPF COLLECT SALES REVENUE

    # Any rando can call get_payout(). Will update amt allowed
    # OR!!! this is where exchange object comes in!!
    earnings = {}
    for acct in predictoors:
        balbefore = OCEAN_bal(acct)
        DT.get_payout(predict_blocknum, OCEAN, predictoors.index(acct), {"from": rando})
        balafter = OCEAN_bal(acct)
        earnings[acct] = balafter - balbefore
        assert balafter > balbefore

    if use_py:
        assert OCEAN_bal(DT.treasurer) == 0.0
    else:
        assert OCEAN_bal(DT) == 0.0
    assert earnings[predictoor2] > earnings[predictoor1]


@enforce_types
class ConvClass:
    def __init__(self, token):
        self.token = token

    def fromWei_balanceOf(self, obj) -> float:
        return from_wei(self.token.balanceOf(obj.address))

    def fromWei_approved(self, obj1, obj2) -> float:
        return from_wei(self.token.allowance(obj1.address, obj2.address))


@enforce_types
def _cur_blocknum() -> int:
    return chain[-1].number

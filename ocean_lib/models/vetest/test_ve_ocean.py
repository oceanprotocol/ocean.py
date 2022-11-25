#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import brownie
import pytest

chain = brownie.network.chain
accounts = brownie.network.accounts
WEEK = 7 * 86400
MAXTIME = 4 * 365 * 86400  # 4 years


@pytest.mark.unit
@pytest.mark.skip(reason="Don't skip, once fixed #1096")
def test_ve_ocean1(config, factory_deployer_wallet, ocean_token, veOCEAN):
    # inspiration from df-py/util/test/veOcean/test_lock.py

    assert veOCEAN.symbol() == "veOCEAN"

    OCEAN = ocean_token

    alice_wallet = accounts.add()  # new account avoids "withdraw old tokens first"
    factory_deployer_wallet.transfer(alice_wallet, "1 ether")

    TA = to_wei(0.0001)
    OCEAN.mint(
        alice_wallet.address,
        TA,
        {"from": factory_deployer_wallet, "gas_limit": chain.block_gas_limit},
    )

    veOCEAN.checkpoint(
        {"from": factory_deployer_wallet, "gas_limit": chain.block_gas_limit}
    )
    OCEAN.approve(
        veOCEAN.address, TA, {"from": alice_wallet, "gas_limit": chain.block_gas_limit}
    )

    t0 = chain.time()
    t1 = t0 // WEEK * WEEK + WEEK  # this is a Thursday, because Jan 1 1970 was
    t2 = t1 + WEEK
    chain.sleep(t1 - t0)

    assert OCEAN.balanceOf(alice_wallet.address) != 0

    veOCEAN.create_lock(
        TA, t2, {"from": alice_wallet, "gas_limit": chain.block_gas_limit}
    )

    assert OCEAN.balanceOf(alice_wallet.address) == 0

    epoch = veOCEAN.user_point_epoch(alice_wallet)
    assert epoch != 0

    assert veOCEAN.get_last_user_slope(alice_wallet) != 0

    alice_vote_power = from_wei(veOCEAN.balanceOf(alice_wallet, chain.time()))
    expected_vote_power = from_wei(TA) * WEEK / MAXTIME
    assert alice_vote_power == pytest.approx(expected_vote_power, TA / 20.0)

    brownie.network.chain.sleep(t2)
    chain.mine()

    veOCEAN.withdraw({"from": alice_wallet, "gas_limit": chain.block_gas_limit})
    assert OCEAN.balanceOf(alice_wallet.address) == TA

    assert veOCEAN.get_last_user_slope(alice_wallet) == 0
    assert veOCEAN.balanceOf(alice_wallet, chain.time()) == 0


def to_wei(amt_eth) -> int:
    return int(amt_eth * 1e18)


def from_wei(amt_wei: int) -> float:
    return float(amt_wei / 1e18)

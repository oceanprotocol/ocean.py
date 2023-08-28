#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import math

import pytest

from ocean_lib.ocean.util import from_wei, send_ether, to_wei

WEEK = 7 * 86400
MAXTIME = 4 * 365 * 86400  # 4 years


@pytest.mark.unit
def test_ve_ocean1(ocean, factory_deployer_wallet, ocean_token):
    OCEAN = ocean.OCEAN_token
    veOCEAN = ocean.veOCEAN

    # inspiration from df-py/util/test/veOcean/test_lock.py
    assert veOCEAN.symbol() == "veOCEAN"

    OCEAN = ocean_token

    web3 = ocean.config_dict["web3_instance"]
    alice_wallet = (
        web3.eth.account.create()
    )  # new account avoids "withdraw old tokens first"
    send_ether(
        ocean.config_dict, factory_deployer_wallet, alice_wallet.address, to_wei(1)
    )

    TA = to_wei(0.0001)
    OCEAN.mint(alice_wallet.address, TA, {"from": factory_deployer_wallet})

    latest_block = web3.eth.get_block("latest")
    veOCEAN.checkpoint({"from": factory_deployer_wallet, "gas": latest_block.gasLimit})
    OCEAN.approve(veOCEAN.address, TA, {"from": alice_wallet})

    latest_block = ocean.config_dict["web3_instance"].eth.get_block("latest")
    t0 = latest_block.timestamp  # ve funcs use block.timestamp, not chain.time()
    t1 = t0 // WEEK * WEEK + WEEK  # this is a Thursday, because Jan 1 1970 was
    t2 = t1 + WEEK

    provider = web3.provider
    provider.make_request("evm_increaseTime", [(t1 - t0)])

    assert OCEAN.balanceOf(alice_wallet.address) != 0

    latest_block = web3.eth.get_block("latest")
    veOCEAN.create_lock(
        TA,
        t2,
        {
            "from": alice_wallet,
            "gas": latest_block.gasLimit,
            "gasPrice": math.ceil(latest_block["baseFeePerGas"] * 1.2),
        },
    )

    assert OCEAN.balanceOf(alice_wallet.address) == 0

    epoch = veOCEAN.user_point_epoch(alice_wallet)
    assert epoch != 0

    assert veOCEAN.get_last_user_slope(alice_wallet) != 0

    latest_block = web3.eth.get_block("latest")
    alice_vote_power = float(
        from_wei(veOCEAN.balanceOf(alice_wallet, latest_block.timestamp))
    )
    expected_vote_power = float(from_wei(TA)) * WEEK / MAXTIME
    assert alice_vote_power == pytest.approx(expected_vote_power, TA / 20.0)

    provider.make_request("evm_increaseTime", [t2])
    provider.make_request("evm_mine", [])

    latest_block = web3.eth.get_block("latest")
    veOCEAN.withdraw(
        {
            "from": alice_wallet,
            "gas": latest_block.gasLimit,
            "gasPrice": math.ceil(latest_block["baseFeePerGas"] * 1.2),
        }
    )
    assert OCEAN.balanceOf(alice_wallet.address) == TA

    latest_block = web3.eth.get_block("latest")
    assert veOCEAN.get_last_user_slope(alice_wallet) == 0
    assert veOCEAN.balanceOf(alice_wallet, latest_block.timestamp) == 0

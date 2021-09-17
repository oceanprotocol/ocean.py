#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models import balancer_constants
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.ocean.util import get_bfactory_address
from ocean_lib.web3_internal.currency import to_wei


def test_complete_flow(
    network, OCEAN_address, alice_wallet, alice_ocean, alice_address, bob_wallet
):
    """Tests a full liquidity add/remove flow."""
    bfactory_address = get_bfactory_address(alice_ocean.config.address_file, network)

    # ===============================================================
    # 1. Alice publishes a dataset (= publishes a datatoken)
    # For now, you're Alice:) Let's proceed.
    DT = alice_ocean.create_data_token(
        "DataToken1", "DT1", alice_wallet, blob="localhost:8030"
    )
    DT_address = DT.address

    # ===============================================================
    # 2. Alice hosts the dataset
    # Do from console:
    # >> touch /var/mydata/myFolder1/file
    # >> ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
    # >> docker run @oceanprotocol/provider-py -e CONFIG=DT

    # ===============================================================
    # 3. Alice mints DTs
    DT.mint(alice_address, to_wei(1000), alice_wallet)

    # ===============================================================
    # 4. Alice creates an OCEAN-DT pool (=a Balancer Pool)
    web3 = alice_ocean.web3
    bfactory = BFactory(web3, bfactory_address)
    pool_address = bfactory.newBPool(from_wallet=alice_wallet)
    pool = BPool(web3, pool_address)

    pool.setPublicSwap(True, from_wallet=alice_wallet)

    pool.setSwapFee(to_wei("0.1"), from_wallet=alice_wallet)  # set 10% fee

    DT.approve(pool_address, to_wei(90), from_wallet=alice_wallet)
    pool.bind(
        DT_address,
        to_wei(90),
        balancer_constants.INIT_WEIGHT_DT,
        from_wallet=alice_wallet,
    )

    OCEAN_token = BToken(web3, OCEAN_address)
    txid = OCEAN_token.approve(pool_address, to_wei(10), from_wallet=alice_wallet)
    r = OCEAN_token.get_tx_receipt(web3, txid)
    assert r and r.status == 1, f"approve failed, receipt={r}"
    pool.bind(
        OCEAN_address,
        to_wei(10),
        balancer_constants.INIT_WEIGHT_OCEAN,
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 5. Alice adds liquidity to pool
    DT.approve(pool_address, to_wei(9), from_wallet=alice_wallet)
    pool.rebind(
        DT_address,
        to_wei(90 + 9),
        balancer_constants.INIT_WEIGHT_DT,
        from_wallet=alice_wallet,
    )

    OCEAN_token.approve(pool_address, to_wei(1), from_wallet=alice_wallet)
    pool.rebind(
        OCEAN_address,
        to_wei(10 + 1),
        balancer_constants.INIT_WEIGHT_OCEAN,
        from_wallet=alice_wallet,
    )

    # 6. Bob buys a DT from pool
    OCEAN_token.approve(pool_address, to_wei(2), from_wallet=bob_wallet)
    pool.swapExactAmountOut(
        tokenIn_address=OCEAN_address,
        maxAmountIn=to_wei(2),
        tokenOut_address=DT_address,
        tokenAmountOut=to_wei(1),
        maxPrice=2 ** 255,
        from_wallet=bob_wallet,
    )

    # ===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>

    # ===============================================================
    # 8. Alice removes liquidity
    pool.rebind(
        DT_address,
        to_wei(90 + 9 - 2),
        balancer_constants.INIT_WEIGHT_DT,
        from_wallet=alice_wallet,
    )
    pool.rebind(
        OCEAN_address,
        to_wei(10 + 1 - 3),
        balancer_constants.INIT_WEIGHT_OCEAN,
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 9. Alice sells data tokens
    DT.approve(pool_address, to_wei(1), from_wallet=alice_wallet)
    pool.swapExactAmountIn(
        tokenIn_address=DT_address,
        tokenAmountIn=to_wei(1),
        tokenOut_address=OCEAN_address,
        minAmountOut=to_wei("0.0001"),
        maxPrice=2 ** 255,
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 10. Alice finalizes pool. Now others can add liquidity.
    pool.finalize(from_wallet=alice_wallet)

    # ===============================================================
    # 11. Bob adds liquidity
    DT.approve(pool_address, to_wei(1), from_wallet=bob_wallet)
    OCEAN_token.approve(pool_address, to_wei(1), from_wallet=bob_wallet)
    pool.joinPool(to_wei("0.1"), [to_wei(1), to_wei(1)], from_wallet=bob_wallet)

    # ===============================================================
    # 12. Bob adds liquidity AGAIN
    DT.approve(pool_address, to_wei(1), from_wallet=bob_wallet)
    OCEAN_token.approve(pool_address, to_wei(1), from_wallet=bob_wallet)
    pool.joinPool(to_wei("0.1"), [to_wei(1), to_wei(1)], from_wallet=bob_wallet)

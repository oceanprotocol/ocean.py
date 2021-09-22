#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.web3_internal.currency import to_wei


def test_quickstart(alice_ocean, alice_wallet, alice_address, bob_ocean, bob_wallet):
    """Tests a simple liquidity add/remove flow."""
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

    pool = alice_ocean.pool.create(
        DT_address,
        data_token_amount=to_wei(90),
        OCEAN_amount=to_wei(10),
        from_wallet=alice_wallet,
    )
    pool_address = pool.address

    assert pool.isFinalized(), "create pool should finalize the pool."
    assert pool.isPublicSwap(), "create pool should have publicSwap enabled."

    # ===============================================================
    # 5. Alice adds liquidity to pool
    alice_ocean.pool.add_data_token_liquidity(
        pool_address, amount=to_wei(9), from_wallet=alice_wallet
    )
    dt_pool_shares = pool.balanceOf(alice_wallet.address)

    alice_ocean.pool.add_OCEAN_liquidity(
        pool_address, amount=to_wei(1), from_wallet=alice_wallet
    )
    ocn_pool_shares = pool.balanceOf(alice_wallet.address)

    # ===============================================================
    # 6. Bob buys a DT from pool
    alice_ocean.pool.buy_data_tokens(
        pool_address,
        amount=to_wei(1),
        max_OCEAN_amount=to_wei(2),
        from_wallet=bob_wallet,
    )

    # ===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>

    # ===============================================================
    # 8. Alice removes liquidity
    alice_ocean.pool.remove_data_token_liquidity(
        pool_address,
        amount=to_wei(2),
        max_pool_shares=dt_pool_shares,
        from_wallet=alice_wallet,
    )

    alice_ocean.pool.remove_OCEAN_liquidity(
        pool_address,
        amount=to_wei(3),
        max_pool_shares=ocn_pool_shares,
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 9. Alice sells data tokens
    alice_ocean.pool.sell_data_tokens(
        pool_address,
        amount=to_wei(1),
        min_OCEAN_amount=to_wei("0.0001"),
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 11. Bob adds liquidity
    bob_ocean.pool.add_data_token_liquidity(
        pool_address, amount=to_wei("0.1"), from_wallet=bob_wallet
    )
    bob_ocean.pool.add_OCEAN_liquidity(
        pool_address, amount=to_wei(1), from_wallet=bob_wallet
    )

    # ===============================================================
    # 12. Bob adds liquidity AGAIN
    bob_ocean.pool.add_data_token_liquidity(
        pool_address, amount=to_wei("0.2"), from_wallet=bob_wallet
    )
    bob_ocean.pool.add_OCEAN_liquidity(
        pool_address, amount=to_wei("0.1"), from_wallet=bob_wallet
    )

    # ===============================================================
    # 13. Get liquidity history
    (
        ocean_liquidity_history,
        dt_liquidity_history,
    ) = bob_ocean.pool.get_liquidity_history(pool_address)
    assert len(ocean_liquidity_history) == 7
    assert len(dt_liquidity_history) == 7


# ===============================================================
# Test helper functions for the quickstart stuff above
def test_ocean_balancer_helpers(
    OCEAN_address, alice_ocean, alice_wallet, alice_address, bob_ocean
):
    DT = alice_ocean.create_data_token("DataToken1", "DT1", alice_wallet, blob="foo")
    DT.mint(alice_address, to_wei(1000), alice_wallet)

    with pytest.raises(Exception):  # not enough liquidity
        pool = alice_ocean.pool.create(
            DT.address, data_token_amount=0, OCEAN_amount=0, from_wallet=alice_wallet
        )

    pool = alice_ocean.pool.create(
        DT.address,
        data_token_amount=to_wei(90),
        OCEAN_amount=to_wei(10),
        from_wallet=alice_wallet,
    )
    pool_address = pool.address

    assert alice_ocean.pool.ocean_address == OCEAN_address
    assert alice_ocean.pool.get_token_address(pool.address) == DT.address

    assert alice_ocean.pool.get(alice_ocean.web3, pool_address).address == pool_address
    assert bob_ocean.pool.get(alice_ocean.web3, pool_address).address == pool_address

    DT_price = bob_ocean.pool.get_token_price(pool_address)
    assert DT_price > 0

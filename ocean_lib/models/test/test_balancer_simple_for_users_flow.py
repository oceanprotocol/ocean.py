#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.ocean_pool import add_liquidity, get_token_address
from ocean_lib.ocean.util import to_base_18


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
    DT.mint(alice_address, to_base_18(1000.0), alice_wallet)

    # ===============================================================
    # 4. Alice creates an OCEAN-DT pool (=a Balancer Pool)

    pool = alice_ocean.create_ocean_pool(
        DT_address, data_token_amount=90.0, OCEAN_amount=10.0, from_wallet=alice_wallet
    )
    pool_address = pool.address

    assert pool.isFinalized(), "create pool should finalize the pool."
    assert pool.isPublicSwap(), "create pool should have publicSwap enabled."

    # ===============================================================
    # 5. Alice adds liquidity to pool
    dt_address = get_token_address(alice_ocean.web3, pool, alice_ocean.OCEAN_address)
    add_liquidity(
        alice_ocean.web3, pool, dt_address, to_base_18(9.0), from_wallet=alice_wallet
    )

    dt_pool_shares = pool.balanceOf(alice_wallet.address)

    add_liquidity(
        alice_ocean.web3,
        pool,
        alice_ocean.OCEAN_address,
        to_base_18(1.0),
        from_wallet=alice_wallet,
    )
    ocn_pool_shares = pool.balanceOf(alice_wallet.address)

    # ===============================================================
    # 6. Bob buys a DT from pool
    alice_ocean.pool.buy_data_tokens(
        pool_address, amount=1.0, max_OCEAN_amount=2.0, from_wallet=bob_wallet
    )

    # ===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>

    # ===============================================================
    # 8. Alice removes liquidity
    alice_ocean.pool.remove_data_token_liquidity(
        pool_address,
        amount_base=to_base_18(2.0),
        max_pool_shares_base=dt_pool_shares,
        from_wallet=alice_wallet,
    )

    alice_ocean.pool.remove_OCEAN_liquidity(
        pool_address,
        amount_base=to_base_18(3.0),
        max_pool_shares_base=ocn_pool_shares,
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 9. Alice sells data tokens
    alice_ocean.pool.sell_data_tokens(
        pool_address,
        amount_base=to_base_18(1.0),
        min_OCEAN_amount_base=to_base_18(0.0001),
        from_wallet=alice_wallet,
    )

    # ===============================================================
    # 11. Bob adds liquidity in data token and then OCEAN
    add_liquidity(
        bob_ocean.web3, pool, dt_address, to_base_18(0.1), from_wallet=bob_wallet
    )
    add_liquidity(
        bob_ocean.web3,
        pool,
        bob_ocean.OCEAN_address,
        to_base_18(1.0),
        from_wallet=bob_wallet,
    )

    # ===============================================================
    # 12. Bob adds liquidity AGAIN (in data token and then OCEAN)
    add_liquidity(
        bob_ocean.web3, pool, dt_address, to_base_18(0.2), from_wallet=bob_wallet
    )
    add_liquidity(
        bob_ocean.web3,
        pool,
        bob_ocean.OCEAN_address,
        to_base_18(0.1),
        from_wallet=bob_wallet,
    )


# ===============================================================
# Test helper functions for the quickstart stuff above
def test_ocean_balancer_helpers(
    OCEAN_address, alice_ocean, alice_wallet, alice_address, bob_ocean
):
    DT = alice_ocean.create_data_token("DataToken1", "DT1", alice_wallet, blob="foo")
    DT.mint(alice_address, to_base_18(1000.0), alice_wallet)

    with pytest.raises(Exception):  # not enough liquidity
        pool = alice_ocean.create_ocean_pool(
            DT.address, data_token_amount=0, OCEAN_amount=0, from_wallet=alice_wallet
        )

    pool = alice_ocean.create_ocean_pool(
        DT.address, data_token_amount=90.0, OCEAN_amount=10.0, from_wallet=alice_wallet
    )
    pool_address = pool.address

    assert alice_ocean.pool.ocean_address == OCEAN_address

    bpool = BPool(alice_ocean.web3, pool_address)
    tokens = bpool.getCurrentTokens()
    assert DT.address in tokens

    assert BPool(alice_ocean.web3, pool_address).address == pool_address
    assert BPool(alice_ocean.web3, pool_address).address == pool_address

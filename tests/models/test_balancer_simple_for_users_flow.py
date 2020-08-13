import pytest

from ocean_lib.ocean.util import to_base_18, from_base_18


def test_quickstart(alice_ocean, alice_wallet, alice_address,
                    bob_ocean, bob_wallet):
    # ===============================================================
    # 1. Alice publishes a dataset (= publishes a datatoken)
    # For now, you're Alice:) Let's proceed.
    DT = alice_ocean.create_data_token('localhost:8030', alice_wallet)
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
    pool = alice_ocean.pool.create(
        DT_address, data_token_amount=90.0, OCEAN_amount=10.0,
        from_wallet=alice_wallet)
    pool_address = pool.address

    assert pool.isFinalized(), f'create pool should finalize the pool.'
    assert pool.isPublicSwap(), f'create pool should have publicSwap enabled.'

    # ===============================================================
    # 5. Alice adds liquidity to pool
    alice_ocean.pool.add_data_token_liquidity(
        pool_address, amount_base=to_base_18(9.0), from_wallet=alice_wallet)
    dt_pool_shares = pool.balanceOf(alice_wallet.address)

    alice_ocean.pool.add_OCEAN_liquidity(
        pool_address, amount_base=to_base_18(1.0), from_wallet=alice_wallet)
    ocn_pool_shares = pool.balanceOf(alice_wallet.address)

    # ===============================================================
    # 6. Bob buys a DT from pool
    alice_ocean.pool.buy_data_tokens(pool_address,
                                     amount_base=to_base_18(1.0),
                                     max_OCEAN_amount_base=to_base_18(2.0),
                                     from_wallet=bob_wallet)

    # ===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>

    # ===============================================================
    # 8. Alice removes liquidity
    alice_ocean.pool.remove_data_token_liquidity(pool_address,
                                                 amount_base=to_base_18(2.0),
                                                 max_pool_shares_base=dt_pool_shares,
                                                 from_wallet=alice_wallet)

    alice_ocean.pool.remove_OCEAN_liquidity(pool_address,
                                            amount_base=to_base_18(3.0),
                                            max_pool_shares_base=ocn_pool_shares,
                                            from_wallet=alice_wallet)

    # ===============================================================
    # 9. Alice sells data tokens
    alice_ocean.pool.sell_data_tokens(pool_address,
                                      amount_base=to_base_18(1.0),
                                      min_OCEAN_amount_base=to_base_18(0.0001),
                                      from_wallet=alice_wallet)

    # ===============================================================
    # 11. Bob adds liquidity
    bob_ocean.pool.add_data_token_liquidity(
        pool_address,
        amount_base=to_base_18(0.1),
        from_wallet=bob_wallet)
    bob_ocean.pool.add_OCEAN_liquidity(
        pool_address,
        amount_base=to_base_18(1.0),
        from_wallet=bob_wallet)

    # ===============================================================
    # 12. Bob adds liquidity AGAIN
    bob_ocean.pool.add_data_token_liquidity(
        pool_address,
        amount_base=to_base_18(0.2),
        from_wallet=bob_wallet)
    bob_ocean.pool.add_OCEAN_liquidity(
        pool_address,
        amount_base=to_base_18(0.1),
        from_wallet=bob_wallet)


# ===============================================================
# Test helper functions for the quickstart stuff above
def test_ocean_balancer_helpers(
        OCEAN_address, alice_ocean, alice_wallet, alice_address, bob_ocean):
    DT = alice_ocean.create_data_token('foo', alice_wallet)
    DT.mint(alice_address, to_base_18(1000.0), alice_wallet)

    with pytest.raises(Exception):  # not enough liquidity
        pool = alice_ocean.pool.create(
            DT.address, data_token_amount=0, OCEAN_amount=0,
            from_wallet=alice_wallet)

    pool = alice_ocean.pool.create(
        DT.address, data_token_amount=90.0, OCEAN_amount=10.0,
        from_wallet=alice_wallet)
    pool_address = pool.address

    assert alice_ocean.pool.ocean_address == OCEAN_address
    assert alice_ocean.pool.get_token_address(pool.address) == DT.address

    assert alice_ocean.pool.get(pool_address).address == pool_address
    assert bob_ocean.pool.get(pool_address).address == pool_address

    DT_price = from_base_18(bob_ocean.pool.get_token_price_base(pool_address))
    assert DT_price > 0.0

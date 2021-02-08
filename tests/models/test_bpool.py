import pytest
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.ocean.util import from_base_18, get_bfactory_address, to_base_18
from ocean_lib.web3_internal.wallet import Wallet
from tests.models.conftest import alice_info

HUGEINT = 2 ** 255


def test_notokens_basic(OCEAN_address, network, alice_wallet, alice_address):
    pool = _deployBPool(network, alice_wallet)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens()  # pool's not finalized
    assert pool.getSwapFee() == to_base_18(1e-6)
    assert pool.getController() == alice_address
    assert str(pool)

    with pytest.raises(Exception):
        pool.finalize()  # can't finalize if no tokens


def test_setSwapFee_works(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    pool.setSwapFee(to_base_18(0.011), from_wallet=alice_wallet)
    assert from_base_18(pool.getSwapFee()) == 0.011


def test_setSwapFee_fails(
    network, alice_wallet, alice_address, bob_wallet, bob_address
):
    factory = BFactory(get_bfactory_address(network))
    pool_address = factory.newBPool(alice_wallet)
    pool = BPool(pool_address)
    with pytest.raises(Exception):
        pool.setSwapFee(
            to_base_18(0.011), from_wallet=bob_wallet
        )  # not ok, bob isn't controller
    pool.setController(bob_address, from_wallet=alice_wallet)
    pool.setSwapFee(to_base_18(0.011), from_wallet=bob_wallet)  # ok now


def test_setController(network, alice_wallet, alice_address, bob_wallet, bob_address):
    pool = _deployBPool(network, alice_wallet)
    pool.setController(bob_address, from_wallet=alice_wallet)
    assert pool.getController() == bob_address

    pool.setController(alice_address, from_wallet=bob_wallet)
    assert pool.getController() == alice_address


def test_setPublicSwap(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    assert pool.isPublicSwap()
    pool.setPublicSwap(False, from_wallet=alice_wallet)
    assert not pool.isPublicSwap()


def test_2tokens_basic(network, T1, T2, alice_wallet, alice_address):
    pool = _deployBPool(network, alice_wallet)
    assert T1.address != T2.address
    assert T1.address != pool.address

    assert from_base_18(T1.balanceOf(alice_address)) >= 90.0
    _ = from_base_18(T2.balanceOf(alice_address)) >= 10.0

    with pytest.raises(Exception):  # can't bind until we approve
        pool.bind(T1.address, to_base_18(90.0), to_base_18(9.0))

    # Bind two tokens to the pool
    T1.approve(pool.address, to_base_18(90.0), from_wallet=alice_wallet)
    T2.approve(pool.address, to_base_18(10.0), from_wallet=alice_wallet)

    assert from_base_18(T1.allowance(alice_address, pool.address)) == 90.0
    assert from_base_18(T2.allowance(alice_address, pool.address)) == 10.0

    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address, to_base_18(90.0), to_base_18(9.0), from_wallet=alice_wallet)
    pool.bind(T2.address, to_base_18(10.0), to_base_18(1.0), from_wallet=alice_wallet)
    assert pool.isBound(T1.address) and pool.isBound(T2.address)

    assert pool.getNumTokens() == 2
    assert pool.getCurrentTokens() == [T1.address, T2.address]

    assert pool.getDenormalizedWeight(T1.address) == to_base_18(9.0)
    assert pool.getDenormalizedWeight(T2.address) == to_base_18(1.0)
    assert pool.getTotalDenormalizedWeight() == to_base_18(9.0 + 1.0)

    assert pool.getNormalizedWeight(T1.address) == to_base_18(0.9)
    assert pool.getNormalizedWeight(T2.address) == to_base_18(0.1)

    assert pool.getBalance(T1.address) == to_base_18(90.0)
    assert pool.getBalance(T2.address) == to_base_18(10.0)

    assert str(pool)


def test_unbind(network, T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 1.0, 1.0, 1.0, 1.0)

    pool.unbind(T1.address, from_wallet=alice_wallet)

    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert from_base_18(pool.getBalance(T2.address)) == 1.0


def test_finalize(network, T1, T2, alice_address, alice_wallet):
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply() == 0
    assert pool.balanceOf(alice_address) == 0
    assert pool.allowance(alice_address, pool.address) == 0

    pool.finalize(from_wallet=alice_wallet)

    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply() == to_base_18(100.0)
    assert pool.balanceOf(alice_address) == to_base_18(100.0)
    assert pool.allowance(alice_address, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]


def test_public_pool(network, bob_wallet):
    alice = alice_info()
    alice_address = alice.address
    bob_address = bob_wallet.address
    T1 = alice.T1
    T2 = alice.T2

    pool = _createPoolWith2Tokens(
        network, alice.T1, alice.T2, alice.wallet, 90.0, 10.0, 9.0, 1.0
    )
    BPT = pool

    # alice give Bob some tokens
    alice.T1.transfer(bob_wallet.address, to_base_18(100.0), from_wallet=alice.wallet)
    alice.T2.transfer(bob_wallet.address, to_base_18(100.0), from_wallet=alice.wallet)

    # verify holdings
    assert from_base_18(alice.T1.balanceOf(alice.address)) == (1000.0 - 90.0 - 100.0)
    assert from_base_18(alice.T2.balanceOf(alice.address)) == (1000.0 - 10.0 - 100.0)
    assert from_base_18(BPT.balanceOf(alice.address)) == 0

    assert from_base_18(alice.T1.balanceOf(bob_address)) == 100.0
    assert from_base_18(alice.T2.balanceOf(bob_address)) == 100.0
    assert from_base_18(BPT.balanceOf(bob_address)) == 0

    assert from_base_18(T1.balanceOf(pool.address)) == 90.0
    assert from_base_18(T2.balanceOf(pool.address)) == 10.0
    assert from_base_18(BPT.balanceOf(pool.address)) == 0

    # finalize
    pool = BPool(pool.address)
    pool.finalize(from_wallet=alice.wallet)

    # verify holdings
    assert from_base_18(alice.T1.balanceOf(alice.address)) == (1000.0 - 90.0 - 100.0)
    assert from_base_18(alice.T2.balanceOf(alice.address)) == (1000.0 - 10.0 - 100.0)
    assert from_base_18(BPT.balanceOf(alice.address)) == 100.0  # new!

    assert from_base_18(T1.balanceOf(pool.address)) == 90.0
    assert from_base_18(T2.balanceOf(pool.address)) == 10.0
    assert from_base_18(BPT.balanceOf(pool.address)) == 0

    # bob join pool. Wants 10 BPT
    T1.approve(pool.address, to_base_18(100.0), from_wallet=bob_wallet)
    T2.approve(pool.address, to_base_18(100.0), from_wallet=bob_wallet)
    pool.joinPool(
        poolAmountOut_base=to_base_18(10.0),  # 10 BPT
        maxAmountsIn_base=[to_base_18(100.0), to_base_18(100.0)],
        from_wallet=bob_wallet,
    )

    # verify holdings
    assert from_base_18(T1.balanceOf(alice_address)) == (1000.0 - 90.0 - 100.0)
    assert from_base_18(T2.balanceOf(alice_address)) == (1000.0 - 10.0 - 100.0)
    assert from_base_18(BPT.balanceOf(alice_address)) == 100.0

    assert from_base_18(T1.balanceOf(bob_address)) == (100.0 - 9.0)
    assert from_base_18(T2.balanceOf(bob_address)) == (100.0 - 1.0)
    assert from_base_18(BPT.balanceOf(bob_address)) == 10.0

    assert from_base_18(T1.balanceOf(pool.address)) == (90.0 + 9.0)
    assert from_base_18(T2.balanceOf(pool.address)) == (10.0 + 1.0)
    assert from_base_18(BPT.balanceOf(pool.address)) == 0

    # bob sells 2 BPT
    # -this is where BLabs fee kicks in. But the fee is currently set to 0.
    pool.exitPool(
        poolAmountIn_base=to_base_18(2.0),
        minAmountsOut_base=[to_base_18(0.0), to_base_18(0.0)],
        from_wallet=bob_wallet,
    )
    assert from_base_18(T1.balanceOf(bob_address)) == 92.8
    assert from_base_18(T2.balanceOf(bob_address)) == 99.2
    assert from_base_18(BPT.balanceOf(bob_address)) == 8.0

    # bob buys 5 more BPT
    pool.joinPool(
        poolAmountOut_base=to_base_18(5.0),
        maxAmountsIn_base=[to_base_18(90.0), to_base_18(90.0)],
        from_wallet=bob_wallet,
    )
    assert from_base_18(BPT.balanceOf(bob_address)) == 13.0

    # bob fully exits
    pool.exitPool(
        poolAmountIn_base=to_base_18(13.0),
        minAmountsOut_base=[to_base_18(0.0), to_base_18(0.0)],
        from_wallet=bob_wallet,
    )
    assert from_base_18(BPT.balanceOf(bob_address)) == 0.0


def test_rebind_more_tokens(network, T1, T2, alice_wallet):
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)

    # insufficient allowance
    with pytest.raises(Exception):
        pool.rebind(
            T1.address, to_base_18(120.0), to_base_18(9.0), from_wallet=alice_wallet
        )

    # sufficient allowance
    T1.approve(pool.address, to_base_18(30.0), from_wallet=alice_wallet)
    pool.rebind(
        T1.address, to_base_18(120.0), to_base_18(9.0), from_wallet=alice_wallet
    )


def test_gulp(network, T1, alice_wallet):
    pool = _deployBPool(network, alice_wallet)

    # bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, to_base_18(50.0), from_wallet=alice_wallet)
    pool.bind(T1.address, to_base_18(2.0), to_base_18(50.0), from_wallet=alice_wallet)

    # T1 is now pool's (a) ERC20 balance (b) _records[token].balance
    assert T1.balanceOf(pool.address) == to_base_18(2.0)  # ERC20 balance
    assert pool.getBalance(T1.address) == to_base_18(2.0)  # records[]

    # but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, to_base_18(5.0), from_wallet=alice_wallet)
    assert T1.balanceOf(pool.address) == to_base_18(2.0 + 5.0)  # ERC20 bal
    assert pool.getBalance(T1.address) == to_base_18(2.0)  # records[]

    # so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address, from_wallet=alice_wallet)
    assert T1.balanceOf(pool.address) == to_base_18(2.0 + 5.0)  # ERC20
    assert pool.getBalance(T1.address) == to_base_18(2.0 + 5.0)  # records[]


def test_spot_price(network, T1, T2, alice_wallet):
    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet, 1.0, 1.0, 1.0, 1.0)
    assert p_sans == 1.0
    assert round(p, 8) == 1.000001

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)
    assert p_sans == 1.0
    assert round(p, 8) == 1.000001

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet, 1.0, 2.0, 1.0, 1.0)
    assert p_sans == 0.5
    assert round(p, 8) == 0.5000005

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet, 2.0, 1.0, 1.0, 1.0)
    assert p_sans == 2.0
    assert round(p, 8) == 2.000002

    (p, p_sans) = _spotPrices(network, T1, T2, alice_wallet, 9.0, 10.0, 9.0, 1.0)
    assert p_sans == 0.1
    assert round(p, 8) == 0.1000001


def _spotPrices(
    network: str,
    T1: BToken,
    T2: BToken,
    wallet: Wallet,
    bal1: float,
    bal2: float,
    w1: float,
    w2: float,
):
    pool = _createPoolWith2Tokens(network, T1, T2, wallet, bal1, bal2, w1, w2)
    a1, a2 = T1.address, T2.address
    return (
        from_base_18(pool.getSpotPrice(a1, a2)),
        from_base_18(pool.getSpotPriceSansFee(a1, a2)),
    )


def test_joinSwapExternAmountIn(network, T1, T2, alice_wallet, alice_address):
    init_T1balance = from_base_18(T1.balanceOf(alice_address))
    T2balance = from_base_18(T2.balanceOf(alice_address))
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)
    T1.approve(pool.address, to_base_18(100.0), from_wallet=alice_wallet)

    # pool's not public
    with pytest.raises(Exception):
        pool.swapExactAmountOut(
            tokenIn_address=T1.address,
            maxAmountIn_base=to_base_18(100.0),
            tokenOut_address=T2.address,
            tokenAmountOut_base=to_base_18(10.0),
            maxPrice_base=HUGEINT,
            from_wallet=alice_wallet,
        )

    # pool's public
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    pool.swapExactAmountOut(
        tokenIn_address=T1.address,
        maxAmountIn_base=to_base_18(100.0),
        tokenOut_address=T2.address,
        tokenAmountOut_base=to_base_18(1.0),
        maxPrice_base=HUGEINT,
        from_wallet=alice_wallet,
    )
    new_balance = init_T1balance - 91.055
    assert (
        (new_balance - 0.005)
        <= from_base_18(T1.balanceOf(alice_address))
        <= (new_balance + 0.005)
    )
    assert from_base_18(T2.balanceOf(alice_address)) == (T2balance - 9.0)


def test_joinswapPoolAmountOut(network, T1, T2, alice_address, alice_wallet):
    T1balance = from_base_18(T1.balanceOf(alice_address))
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = from_base_18(BPT.balanceOf(alice_address))
    T1.approve(pool.address, to_base_18(90.0), from_wallet=alice_wallet)
    assert from_base_18(T1.balanceOf(alice_address)) == (T1balance - 90)
    T1balance = from_base_18(T1.balanceOf(alice_address))
    pool.joinswapPoolAmountOut(
        tokenIn_address=T1.address,
        poolAmountOut_base=to_base_18(10.0),  # BPT wanted
        maxAmountIn_base=to_base_18(90.0),  # max T1 to spend
        from_wallet=alice_wallet,
    )
    assert from_base_18(T1.balanceOf(alice_address)) >= (T1balance - 90.0)
    assert from_base_18(BPT.balanceOf(alice_address)) == (pool_balance + 10.0)


def test_exitswapPoolAmountIn(network, T1, T2, alice_address, alice_wallet):
    T1balance = from_base_18(T1.balanceOf(alice_address))
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = from_base_18(BPT.balanceOf(alice_address))
    assert from_base_18(T1.balanceOf(alice_address)) == (T1balance - 90)
    pool.exitswapPoolAmountIn(
        tokenOut_address=T1.address,
        poolAmountIn_base=to_base_18(10.0),  # BPT spent
        minAmountOut_base=to_base_18(1.0),  # min T1 wanted
        from_wallet=alice_wallet,
    )
    assert from_base_18(T1.balanceOf(alice_address)) >= (T1balance - 90 + 1.0)
    assert from_base_18(BPT.balanceOf(alice_address)) == (pool_balance - 10.0)


def test_exitswapExternAmountOut(network, T1, T2, alice_address, alice_wallet):
    T1balance = from_base_18(T1.balanceOf(alice_address))
    pool = _createPoolWith2Tokens(network, T1, T2, alice_wallet, 90.0, 10.0, 9.0, 1.0)
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = from_base_18(BPT.balanceOf(alice_address))
    assert from_base_18(T1.balanceOf(alice_address)) == T1balance - 90
    pool.exitswapExternAmountOut(
        tokenOut_address=T1.address,
        tokenAmountOut_base=to_base_18(2.0),  # T1 wanted
        maxPoolAmountIn_base=to_base_18(10.0),  # max BPT spent
        from_wallet=alice_wallet,
    )
    assert from_base_18(T1.balanceOf(alice_address)) == (T1balance - 90 + 2.0)
    assert from_base_18(BPT.balanceOf(alice_address)) >= (pool_balance - 10.0)


def test_calcSpotPrice_base(network, T1, T2, alice_address, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcSpotPrice(
        tokenBalanceIn_base=to_base_18(10.0),
        tokenWeightIn_base=to_base_18(1.0),
        tokenBalanceOut_base=to_base_18(11.0),
        tokenWeightOut_base=to_base_18(1.0),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 0.909


def test_calcOutGivenIn_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcOutGivenIn(
        tokenBalanceIn_base=to_base_18(10.0),
        tokenWeightIn_base=to_base_18(1.0),
        tokenBalanceOut=to_base_18(10.1),
        tokenWeightOut_base=to_base_18(1.0),
        tokenAmountIn_base=to_base_18(1.0),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 0.918


def test_calcInGivenOut_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcInGivenOut(
        tokenBalanceIn_base=to_base_18(10.0),
        tokenWeightIn_base=to_base_18(1.0),
        tokenBalanceOut_base=to_base_18(10.1),
        tokenWeightOut_base=to_base_18(1.0),
        tokenAmountOut_base=to_base_18(1.0),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 1.099


def test_calcPoolOutGivenSingleIn_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcPoolOutGivenSingleIn(
        tokenBalanceIn_base=to_base_18(10.0),
        tokenWeightIn_base=to_base_18(1.0),
        poolSupply_base=to_base_18(120.0),
        totalWeight_base=to_base_18(2.0),
        tokenAmountIn_base=to_base_18(0.1),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 0.599


def test_calcSingleInGivenPoolOut_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcSingleInGivenPoolOut(
        tokenBalanceIn_base=to_base_18(10.0),
        tokenWeightIn_base=to_base_18(1.0),
        poolSupply_base=to_base_18(120.0),
        totalWeight_base=to_base_18(2.0),
        poolAmountOut_base=to_base_18(10.0),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 1.736


def test_calcSingleOutGivenPoolIn_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcSingleOutGivenPoolIn(
        tokenBalanceOut_base=to_base_18(10.0),
        tokenWeightOut_base=to_base_18(1.0),
        poolSupply_base=to_base_18(120.0),
        totalWeight_base=to_base_18(2.0),
        poolAmountIn_base=to_base_18(10.0),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 1.597


def test_calcPoolInGivenSingleOut_base(network, alice_wallet):
    pool = _deployBPool(network, alice_wallet)
    x = pool.calcPoolInGivenSingleOut(
        tokenBalanceOut_base=to_base_18(1000.0),
        tokenWeightOut_base=to_base_18(5.0),
        poolSupply_base=to_base_18(100.0),
        totalWeight_base=to_base_18(10.0),
        tokenAmountOut_base=to_base_18(0.1),
        swapFee_base=0,
    )
    assert round(from_base_18(x), 3) == 0.005


def _createPoolWith2Tokens(
    network: str,
    T1: BToken,
    T2: BToken,
    wallet: Wallet,
    bal1: float,
    bal2: float,
    w1: float,
    w2: float,
):
    pool = _deployBPool(network, wallet)

    T1.get_tx_receipt(T1.approve(pool.address, to_base_18(bal1), from_wallet=wallet))
    T2.get_tx_receipt(T2.approve(pool.address, to_base_18(bal2), from_wallet=wallet))

    if pool.isBound(T1.address):
        pool.unbind(T1.address, wallet)

    if pool.isBound(T2.address):
        pool.unbind(T2.address, wallet)

    pool.bind(T1.address, to_base_18(bal1), to_base_18(w1), from_wallet=wallet)
    pool.bind(T2.address, to_base_18(bal2), to_base_18(w2), from_wallet=wallet)

    return pool


def _deployBPool(network: str, from_wallet: Wallet) -> BPool:
    factory_address = get_bfactory_address(network)
    factory = BFactory(factory_address)
    pool_address = factory.newBPool(from_wallet=from_wallet)
    pool = BPool(pool_address)
    return pool

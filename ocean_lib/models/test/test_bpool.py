#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal
from typing import Union

import pytest
from enforce_typing import enforce_types
from ocean_lib.config import Config
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models.test.conftest import alice_info
from ocean_lib.ocean.util import get_bfactory_address
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from web3.main import Web3

HUGEINT = 2 ** 255


def test_notokens_basic(
    OCEAN_address, network, web3, config, alice_wallet, alice_address
):
    """Tests deployment of a pool without tokens."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert not pool.isBound(OCEAN_address)
    assert pool.getNumTokens() == 0
    assert pool.getCurrentTokens() == []
    with pytest.raises(Exception):
        pool.getFinalTokens()  # pool's not finalized
    assert pool.getSwapFee() == to_wei("1e-6")
    assert pool.getController() == alice_address
    assert str(pool)

    with pytest.raises(Exception):
        pool.finalize(from_wallet=alice_wallet)  # can't finalize if no tokens


def test_setSwapFee_works(network, config, web3, alice_wallet):
    """Tests that a swap fee can be set on the pool by the controller of that pool."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    pool.setSwapFee(to_wei("0.011"), from_wallet=alice_wallet)
    assert pool.getSwapFee() == to_wei("0.011")


def test_setSwapFee_fails(
    network, config, web3, alice_wallet, alice_address, bob_wallet, bob_address
):
    """Tests that someone who isn't a controller can not set the swap fee."""
    factory = BFactory(web3, get_bfactory_address(config.address_file, network))
    pool_address = factory.newBPool(alice_wallet)
    pool = BPool(web3, pool_address)
    with pytest.raises(Exception):
        pool.setSwapFee(
            to_wei("0.011"), from_wallet=bob_wallet
        )  # not ok, bob isn't controller
    pool.setController(bob_address, from_wallet=alice_wallet)
    pool.setSwapFee(to_wei("0.011"), from_wallet=bob_wallet)  # ok now


def test_setController(
    network, config, web3, alice_wallet, alice_address, bob_wallet, bob_address
):
    """Tests that the controller of a pool can be changed."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    pool.setController(bob_address, from_wallet=alice_wallet)
    assert pool.getController() == bob_address

    pool.setController(alice_address, from_wallet=bob_wallet)
    assert pool.getController() == alice_address


def test_setPublicSwap(network, config, web3, alice_wallet):
    """Tests that a pool can be set as public."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    assert pool.isPublicSwap()
    pool.setPublicSwap(False, from_wallet=alice_wallet)
    assert not pool.isPublicSwap()


def test_2tokens_basic(network, config, web3, T1, T2, alice_wallet, alice_address):
    """Tests the deployment of a pool containing 2 tokens (basic happy flow)."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    assert T1.address != T2.address
    assert T1.address != pool.address

    assert T1.balanceOf(alice_address) >= to_wei(90)
    _ = T2.balanceOf(alice_address) >= to_wei(10)

    with pytest.raises(Exception):  # can't bind until we approve
        pool.bind(T1.address, to_wei(90), to_wei(9), from_wallet=alice_wallet)

    # Bind two tokens to the pool
    T1.approve(pool.address, to_wei(90), from_wallet=alice_wallet)
    T2.approve(pool.address, to_wei(10), from_wallet=alice_wallet)

    assert T1.allowance(alice_address, pool.address) == to_wei(90)
    assert T2.allowance(alice_address, pool.address) == to_wei(10)

    assert not pool.isBound(T1.address) and not pool.isBound(T1.address)
    pool.bind(T1.address, to_wei(90), to_wei(9), from_wallet=alice_wallet)
    pool.bind(T2.address, to_wei(10), to_wei(1), from_wallet=alice_wallet)
    assert pool.isBound(T1.address) and pool.isBound(T2.address)

    assert pool.getNumTokens() == 2
    assert pool.getCurrentTokens() == [T1.address, T2.address]

    assert pool.getDenormalizedWeight(T1.address) == to_wei(9)
    assert pool.getDenormalizedWeight(T2.address) == to_wei(1)
    assert pool.getTotalDenormalizedWeight() == to_wei(10)

    assert pool.getNormalizedWeight(T1.address) == to_wei("0.9")
    assert pool.getNormalizedWeight(T2.address) == to_wei("0.1")

    assert pool.getBalance(T1.address) == to_wei(90)
    assert pool.getBalance(T2.address) == to_wei(10)

    assert str(pool)


def test_unbind(network, config, web3, T1, T2, alice_wallet):
    """Tests that a pool can be unbound."""
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 1, 1, 1, 1
    )

    pool.unbind(T1.address, from_wallet=alice_wallet)

    assert pool.getNumTokens() == 1
    assert pool.getCurrentTokens() == [T2.address]
    assert pool.getBalance(T2.address) == to_wei(1)


def test_finalize(network, config, web3, T1, T2, alice_address, alice_wallet):
    """Tests that a pool containing tokens can be finalized."""
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )

    assert not pool.isPublicSwap()
    assert not pool.isFinalized()
    assert pool.totalSupply() == 0
    assert pool.balanceOf(alice_address) == 0
    assert pool.allowance(alice_address, pool.address) == 0

    pool.finalize(from_wallet=alice_wallet)
    assert str(pool) != ""

    assert pool.isPublicSwap()
    assert pool.isFinalized()
    assert pool.totalSupply() == to_wei(100)
    assert pool.balanceOf(alice_address) == to_wei(100)
    assert pool.allowance(alice_address, pool.address) == 0

    assert pool.getFinalTokens() == [T1.address, T2.address]
    assert pool.getCurrentTokens() == [T1.address, T2.address]


def test_public_pool(network, config, bob_wallet, alice_ocean):
    """Tests successful transfers inside a public pool."""
    alice = alice_info()
    alice_address = alice.address
    bob_address = bob_wallet.address
    T1 = alice.T1
    T2 = alice.T2

    pool = _createPoolWith2Tokens(
        network,
        config,
        alice_ocean.web3,
        alice.T1,
        alice.T2,
        alice.wallet,
        90,
        10,
        9,
        1,
    )
    BPT = pool

    # alice give Bob some tokens
    alice.T1.transfer(bob_wallet.address, to_wei(100), from_wallet=alice.wallet)
    alice.T2.transfer(bob_wallet.address, to_wei(100), from_wallet=alice.wallet)

    # verify holdings
    assert alice.T1.balanceOf(alice.address) == to_wei(1000 - 90 - 100)  # 810
    assert alice.T2.balanceOf(alice.address) == to_wei(1000 - 10 - 100)  # 890
    assert BPT.balanceOf(alice.address) == to_wei(0)

    assert alice.T1.balanceOf(bob_address) == to_wei(100)
    assert alice.T2.balanceOf(bob_address) == to_wei(100)
    assert BPT.balanceOf(bob_address) == to_wei(0)

    assert T1.balanceOf(pool.address) == to_wei(90)
    assert T2.balanceOf(pool.address) == to_wei(10)
    assert BPT.balanceOf(pool.address) == to_wei(0)

    # finalize
    pool = BPool(alice_ocean.web3, pool.address)
    pool.finalize(from_wallet=alice.wallet)

    # verify holdings
    assert alice.T1.balanceOf(alice.address) == to_wei(1000 - 90 - 100)
    assert alice.T2.balanceOf(alice.address) == to_wei(1000 - 10 - 100)
    assert BPT.balanceOf(alice.address) == to_wei(100)  # new!

    assert T1.balanceOf(pool.address) == to_wei(90)
    assert T2.balanceOf(pool.address) == to_wei(10)
    assert BPT.balanceOf(pool.address) == to_wei(0)

    # bob join pool. Wants 10 BPT
    T1.approve(pool.address, to_wei(100), from_wallet=bob_wallet)
    T2.approve(pool.address, to_wei(100), from_wallet=bob_wallet)
    pool.joinPool(
        poolAmountOut=to_wei(10),  # 10 BPT
        maxAmountsIn=[to_wei(100), to_wei(100)],
        from_wallet=bob_wallet,
    )

    # verify holdings
    assert T1.balanceOf(alice_address) == to_wei(1000 - 90 - 100)  # 810
    assert T2.balanceOf(alice_address) == to_wei(1000 - 10 - 100)  # 890
    assert BPT.balanceOf(alice_address) == to_wei(100)

    assert T1.balanceOf(bob_address) == to_wei(100 - 9)  # 91
    assert T2.balanceOf(bob_address) == to_wei(100 - 1)  # 99
    assert BPT.balanceOf(bob_address) == to_wei(10)

    assert T1.balanceOf(pool.address) == to_wei(90 + 9)  # 99
    assert T2.balanceOf(pool.address) == to_wei(10 + 1)  # 11
    assert BPT.balanceOf(pool.address) == to_wei(0)

    # bob sells 2 BPT
    # -this is where BLabs fee kicks in. But the fee is currently set to 0.
    pool.exitPool(
        poolAmountIn=to_wei(2),
        minAmountsOut=[to_wei(0), to_wei(0)],
        from_wallet=bob_wallet,
    )
    assert T1.balanceOf(bob_address) == 92800000000000000018  # 92.8
    assert T2.balanceOf(bob_address) == 99200000000000000002  # 99.2
    assert BPT.balanceOf(bob_address) == to_wei(8)

    # bob buys 5 more BPT
    pool.joinPool(
        poolAmountOut=to_wei(5),
        maxAmountsIn=[to_wei(90), to_wei(90)],
        from_wallet=bob_wallet,
    )
    assert BPT.balanceOf(bob_address) == to_wei(13)

    # bob fully exits
    pool.exitPool(poolAmountIn=to_wei(13), minAmountsOut=[0, 0], from_wallet=bob_wallet)
    assert BPT.balanceOf(bob_address) == to_wei(0)

    block = alice_ocean.web3.eth.block_number
    block_confirmations = alice_ocean.config.block_confirmations.value
    join_log = pool.get_join_logs(block - (block_confirmations + 1), block)[0]
    assert join_log["args"]["tokenIn"] == T1.address


def test_rebind_more_tokens(network, config, web3, T1, T2, alice_wallet):
    """Tests that we can rebind more tokens on a pool."""
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )

    # insufficient allowance
    with pytest.raises(Exception):
        pool.rebind(T1.address, to_wei(120), to_wei(9), from_wallet=alice_wallet)

    # sufficient allowance
    T1.approve(pool.address, to_wei(30), from_wallet=alice_wallet)
    pool.rebind(T1.address, to_wei(120), to_wei(9), from_wallet=alice_wallet)


def test_gulp(network, config, web3, T1, alice_wallet):
    """Test pool gulp."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)

    # bind T1 to the pool, with a balance of 2.0
    T1.approve(pool.address, to_wei(50), from_wallet=alice_wallet)
    pool.bind(T1.address, to_wei(2), to_wei(50), from_wallet=alice_wallet)

    # T1 is now pool's (a) ERC20 balance (b) _records[token].balance
    assert T1.balanceOf(pool.address) == to_wei(2)  # ERC20 balance
    assert pool.getBalance(T1.address) == to_wei(2)  # records[]

    # but then some joker accidentally sends 5.0 tokens to the pool's address
    #  rather than binding / rebinding. So it's in ERC20 bal but not records[]
    T1.transfer(pool.address, to_wei(5), from_wallet=alice_wallet)
    assert T1.balanceOf(pool.address) == to_wei(2 + 5)  # ERC20 bal
    assert pool.getBalance(T1.address) == to_wei(2)  # records[]

    # so, 'gulp' gets the pool to absorb the tokens into its balances.
    # i.e. to update _records[token].balance to be in sync with ERC20 balance
    pool.gulp(T1.address, from_wallet=alice_wallet)
    assert T1.balanceOf(pool.address) == to_wei(2 + 5)  # ERC20
    assert pool.getBalance(T1.address) == to_wei(2 + 5)  # records[]


def test_spot_price(network, config, web3, T1, T2, alice_wallet):
    """Test calculation of prices on spot."""
    (price, price_sans_fee) = _spotPrices(
        network, config, web3, T1, T2, alice_wallet, 1, 1, 1, 1
    )
    assert price_sans_fee == to_wei(1)
    assert price == to_wei("1.000001000001000001")

    (price, price_sans_fee) = _spotPrices(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )
    assert price_sans_fee == to_wei(1)
    assert price == to_wei("1.000001000001000001")

    (price, price_sans_fee) = _spotPrices(
        network, config, web3, T1, T2, alice_wallet, 1, 2, 1, 1
    )
    assert price_sans_fee == to_wei("0.5")
    assert price == to_wei("0.500000500000500001")

    (price, price_sans_fee) = _spotPrices(
        network, config, web3, T1, T2, alice_wallet, 2, 1, 1, 1
    )
    assert price_sans_fee == to_wei(2)
    assert price == to_wei("2.000002000002000002")

    (price, price_sans_fee) = _spotPrices(
        network, config, web3, T1, T2, alice_wallet, 9, 10, 9, 1
    )
    assert price_sans_fee == to_wei("0.1")
    assert price == to_wei("0.100000100000100000")


def test_joinSwapExternAmountIn(
    network, config, web3, T1, T2, alice_wallet, alice_address
):
    """Tests adding an external amount inside a pool.

    When the pool is not public, assert that an Exception is thrown.
    When the pool is public, assert that the swap is made and the correct balance remains.
    """
    init_T1balance = T1.balanceOf(alice_address)
    T2balance = T2.balanceOf(alice_address)
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )
    T1.approve(pool.address, to_wei(100), from_wallet=alice_wallet)

    # pool's not public
    with pytest.raises(Exception):
        pool.swapExactAmountOut(
            tokenIn_address=T1.address,
            maxAmountIn=to_wei(100),
            tokenOut_address=T2.address,
            tokenAmountOut=to_wei(10),
            maxPrice=HUGEINT,
            from_wallet=alice_wallet,
        )

    # pool's public
    pool.setPublicSwap(True, from_wallet=alice_wallet)
    pool.swapExactAmountOut(
        tokenIn_address=T1.address,
        maxAmountIn=to_wei(100),
        tokenOut_address=T2.address,
        tokenAmountOut=to_wei(1),
        maxPrice=HUGEINT,
        from_wallet=alice_wallet,
    )
    new_balance = init_T1balance - to_wei("91.055")
    assert (
        new_balance - to_wei("0.005")
        <= T1.balanceOf(alice_address)
        <= new_balance + to_wei("0.005")
    )
    assert T2.balanceOf(alice_address) == T2balance - to_wei(9)

    block = web3.eth.block_number
    block_confirmations = config.block_confirmations.value
    swap_log = pool.get_swap_logs(block - (block_confirmations + 1), block)[0]
    assert swap_log["args"]["tokenIn"] == T1.address


def test_joinswapPoolAmountOut(
    network, config, web3, T1, T2, alice_address, alice_wallet
):
    """Tests taking an amount out of the pool."""
    T1balance = T1.balanceOf(alice_address)
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = BPT.balanceOf(alice_address)
    T1.approve(pool.address, to_wei(90), from_wallet=alice_wallet)
    assert T1.balanceOf(alice_address) == T1balance - to_wei(90)
    T1balance = T1.balanceOf(alice_address)
    pool.joinswapPoolAmountOut(
        tokenIn_address=T1.address,
        poolAmountOut=to_wei(10),  # BPT wanted
        maxAmountIn=to_wei(90),  # max T1 to spend
        from_wallet=alice_wallet,
    )
    assert T1.balanceOf(alice_address) >= T1balance - to_wei(90)
    assert BPT.balanceOf(alice_address) == pool_balance + to_wei(10)


def test_exitswapPoolAmountIn(
    network, config, web3, T1, T2, alice_address, alice_wallet
):
    T1balance = T1.balanceOf(alice_address)
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = BPT.balanceOf(alice_address)
    assert T1.balanceOf(alice_address) == T1balance - to_wei(90)
    pool.exitswapPoolAmountIn(
        tokenOut_address=T1.address,
        poolAmountIn=to_wei(10),  # BPT spent
        minAmountOut=to_wei(1),  # min T1 wanted
        from_wallet=alice_wallet,
    )
    assert T1.balanceOf(alice_address) >= T1balance - to_wei(90) + to_wei(1)
    assert BPT.balanceOf(alice_address) == pool_balance - to_wei(10)


def test_exitswapExternAmountOut(
    network, config, web3, T1, T2, alice_address, alice_wallet, alice_ocean
):
    T1balance = T1.balanceOf(alice_address)
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, alice_wallet, 90, 10, 9, 1
    )
    BPT = pool
    pool.finalize(from_wallet=alice_wallet)
    pool_balance = BPT.balanceOf(alice_address)
    assert T1.balanceOf(alice_address) == T1balance - to_wei(90)
    pool.exitswapExternAmountOut(
        tokenOut_address=T1.address,
        tokenAmountOut=to_wei(2),  # T1 wanted
        maxPoolAmountIn=to_wei(10),  # max BPT spent
        from_wallet=alice_wallet,
    )
    assert T1.balanceOf(alice_address) == T1balance - to_wei(90) + to_wei(2)
    assert BPT.balanceOf(alice_address) >= pool_balance - to_wei(10)

    block = alice_ocean.web3.eth.block_number
    block_confirmations = config.block_confirmations.value
    exit_log = pool.get_exit_logs(block - (block_confirmations + 1), block)[0]
    assert exit_log["args"]["tokenOut"] == T1.address


def test_calcSpotPrice(network, config, web3, T1, T2, alice_address, alice_wallet):
    """Tests pricing with calcSpotPrice."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcSpotPrice(
        tokenBalanceIn=to_wei(10),
        tokenWeightIn=to_wei(1),
        tokenBalanceOut=to_wei(11),
        tokenWeightOut=to_wei(1),
        swapFee=0,
    )
    assert x == to_wei("0.909090909090909091")


def test_calcOutGivenIn(network, config, web3, alice_wallet):
    """Tests pricing with calcOutGivenIn."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcOutGivenIn(
        tokenBalanceIn=to_wei(10),
        tokenWeightIn=to_wei(1),
        tokenBalanceOut=to_wei("10.1"),
        tokenWeightOut=to_wei(1),
        tokenAmountIn=to_wei(1),
        swapFee=0,
    )
    assert x == to_wei("0.918181818181818181")


def test_calcInGivenOut(network, config, web3, alice_wallet):
    """Tests pricing with calcInGivenOut."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcInGivenOut(
        tokenBalanceIn=to_wei(10),
        tokenWeightIn=to_wei(1),
        tokenBalanceOut=to_wei("10.1"),
        tokenWeightOut=to_wei(1),
        tokenAmountOut=to_wei(1),
        swapFee=0,
    )
    assert x == to_wei("1.098901098901098900")


def test_calcPoolOutGivenSingleIn(network, config, web3, alice_wallet):
    """Tests calculations with calcPoolOutGivenSingleIn."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcPoolOutGivenSingleIn(
        tokenBalanceIn=to_wei(10),
        tokenWeightIn=to_wei(1),
        poolSupply=to_wei(120),
        totalWeight=to_wei(2),
        tokenAmountIn=to_wei("0.1"),
        swapFee=0,
    )
    assert x == to_wei("0.598507453453125000")


def test_calcSingleInGivenPoolOut(network, config, web3, alice_wallet):
    """Tests pricing with calcSingleInGivenPoolOut."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcSingleInGivenPoolOut(
        tokenBalanceIn=to_wei(10),
        tokenWeightIn=to_wei(1),
        poolSupply=to_wei(120),
        totalWeight=to_wei(2),
        poolAmountOut=to_wei(10),
        swapFee=0,
    )
    assert x == to_wei("1.736111111111111100")


def test_calcSingleOutGivenPoolIn(network, config, web3, alice_wallet):
    """Tests pricing with calcSingleOutGivenPoolIn."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcSingleOutGivenPoolIn(
        tokenBalanceOut=to_wei(10),
        tokenWeightOut=to_wei(1),
        poolSupply=to_wei(120),
        totalWeight=to_wei(2),
        poolAmountIn=to_wei(10),
        swapFee=0,
    )
    assert x == to_wei("1.597222222222222220")


def test_calcPoolInGivenSingleOut(network, config, web3, alice_wallet):
    """Tests calculations with calcPoolInGivenSingleOut."""
    pool = _deployBPool(web3, config.address_file, network, alice_wallet)
    x = pool.calcPoolInGivenSingleOut(
        tokenBalanceOut=to_wei(1000),
        tokenWeightOut=to_wei(5),
        poolSupply=to_wei(100),
        totalWeight=to_wei(10),
        tokenAmountOut=to_wei("0.1"),
        swapFee=0,
    )
    assert x == to_wei("0.005000125006250000")


@enforce_types
def _createPoolWith2Tokens(
    network: str,
    config: Config,
    web3: Web3,
    T1: BToken,
    T2: BToken,
    wallet: Wallet,
    bal1: Union[Decimal, str, int],
    bal2: Union[Decimal, str, int],
    w1: Union[Decimal, str, int],
    w2: Union[Decimal, str, int],
):
    """Helper function to create a basic pool containing 2 tokens."""
    pool = _deployBPool(web3, config.address_file, network, wallet)

    T1.get_tx_receipt(web3, T1.approve(pool.address, to_wei(bal1), from_wallet=wallet))
    T2.get_tx_receipt(web3, T2.approve(pool.address, to_wei(bal2), from_wallet=wallet))

    if pool.isBound(T1.address):
        pool.unbind(T1.address, wallet)

    if pool.isBound(T2.address):
        pool.unbind(T2.address, wallet)

    pool.bind(T1.address, to_wei(bal1), to_wei(w1), from_wallet=wallet)
    pool.bind(T2.address, to_wei(bal2), to_wei(w2), from_wallet=wallet)

    return pool


@enforce_types
def _deployBPool(
    web3: Web3, address_file: str, network: str, from_wallet: Wallet
) -> BPool:
    """Helper function to deploy a pool."""
    factory_address = get_bfactory_address(address_file, network)
    factory = BFactory(web3, factory_address)
    pool_address = factory.newBPool(from_wallet=from_wallet)
    pool = BPool(web3, pool_address)

    return pool


@enforce_types
def _spotPrices(
    network: str,
    config: Config,
    web3: Web3,
    T1: BToken,
    T2: BToken,
    wallet: Wallet,
    bal1: Union[Decimal, str, int],
    bal2: Union[Decimal, str, int],
    w1: Union[Decimal, str, int],
    w2: Union[Decimal, str, int],
):
    """Helper function to allow for spot price calculations."""
    pool = _createPoolWith2Tokens(
        network, config, web3, T1, T2, wallet, bal1, bal2, w1, w2
    )
    a1, a2 = T1.address, T2.address
    return (pool.getSpotPrice(a1, a2), pool.getSpotPriceSansFee(a1, a2))

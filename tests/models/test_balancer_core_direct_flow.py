import sys

from ocean_lib import Ocean
from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.spool import SPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models import balancer_constants
from ocean_lib.ocean import util
from ocean_lib.ocean.util import toBase18

def test1(network, OCEAN_address,
          alice_wallet, alice_ocean, alice_address,
          bob_wallet):
    web3 = alice_wallet.web3
    sfactory_address = util.confFileValue(network, 'SFACTORY_ADDRESS')
        
    #===============================================================
    # 1. Alice publishes a dataset (= publishes a datatoken)
    # For now, you're Alice:) Let's proceed.
    DT = alice_ocean.create_data_token('localhost:8030', alice_wallet)
    DT_address = DT.address
    
    #===============================================================
    # 2. Alice hosts the dataset
    # Do from console:
    # >> touch /var/mydata/myFolder1/file
    # >> ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
    # >> docker run @oceanprotocol/provider-py -e CONFIG=DT
    
    #===============================================================
    # 3. Alice mints DTs
    DT.mint(alice_address, toBase18(1000.0), alice_wallet)
    
    #===============================================================
    # 4. Alice creates an OCEAN-DT pool (=a Balancer Pool)
    sfactory = SFactory(web3, sfactory_address)
    pool_address = sfactory.newSPool(from_wallet=alice_wallet)
    pool = SPool(web3, pool_address)

    pool.setPublicSwap(True, from_wallet=alice_wallet)

    pool.setSwapFee(toBase18(0.1), from_wallet=alice_wallet) #set 10% fee

    DT.approve(pool_address, toBase18(90.0), from_wallet=alice_wallet)
    pool.bind(DT_address, toBase18(90.0), balancer_constants.INIT_WEIGHT_DT,
              from_wallet=alice_wallet)

    OCEAN_token = BToken(web3, OCEAN_address)
    OCEAN_token.approve(pool_address, toBase18(10.0), from_wallet=alice_wallet)
    pool.bind(OCEAN_address, toBase18(10.0), balancer_constants.INIT_WEIGHT_OCEAN,
              from_wallet=alice_wallet)
    
    #===============================================================
    # 5. Alice adds liquidity to pool
    DT.approve(pool_address, toBase18(9.0), from_wallet=alice_wallet)
    pool.rebind(DT_address, toBase18(90.0+9.0), balancer_constants.INIT_WEIGHT_DT,
                from_wallet=alice_wallet)
    
    OCEAN_token.approve(pool_address, toBase18(1.0), from_wallet=alice_wallet)
    pool.rebind(OCEAN_address, toBase18(10.0+1.0), balancer_constants.INIT_WEIGHT_OCEAN,
                from_wallet=alice_wallet)
    
    # 6. Bob buys a DT from pool
    OCEAN_token.approve(pool_address, toBase18(2.0), from_wallet=bob_wallet)
    pool.swapExactAmountOut(
        tokenIn_address = OCEAN_address,
        maxAmountIn_base = toBase18(2.0),
        tokenOut_address = DT_address,
        tokenAmountOut_base = toBase18(1.0),         
        maxPrice_base = 2 ** 255,
        from_wallet=bob_wallet
    )
    
    #===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>
    
    #===============================================================
    # 8. Alice removes liquidity
    pool.rebind(DT_address, toBase18(90.0+9.0-2.0),
                balancer_constants.INIT_WEIGHT_DT,
                from_wallet=alice_wallet)
    pool.rebind(OCEAN_address, toBase18(10.0+1.0-3.0),
                balancer_constants.INIT_WEIGHT_OCEAN,
                from_wallet=alice_wallet)
    
    #===============================================================
    # 9. Alice sells data tokens
    DT.approve(pool_address, toBase18(1.0), from_wallet=alice_wallet)
    pool.swapExactAmountIn(
        tokenIn_address = DT_address,
        tokenAmountIn_base = toBase18(1.0),
        tokenOut_address = OCEAN_address,
        minAmountOut_base = toBase18(0.0001),
        maxPrice_base = 2 ** 255,
        from_wallet=alice_wallet,
    )
    
    #===============================================================
    # 10. Alice finalizes pool. Now others can add liquidity.
    pool.finalize(from_wallet=alice_wallet)
    
    #===============================================================
    # 11. Bob adds liquidity
    DT.approve(pool_address, toBase18(1.0), from_wallet=bob_wallet)
    OCEAN_token.approve(pool_address, toBase18(1.0), from_wallet=bob_wallet)
    pool.joinPool(toBase18(0.1), [toBase18(1.0), toBase18(1.0)],
                  from_wallet=bob_wallet)
    
    #===============================================================
    # 12. Bob adds liquidity AGAIN
    DT.approve(pool_address, toBase18(1.0), from_wallet=bob_wallet)
    OCEAN_token.approve(pool_address, toBase18(1.0), from_wallet=bob_wallet)
    pool.joinPool(toBase18(0.1), [toBase18(1.0), toBase18(1.0)],
                  from_wallet=bob_wallet)

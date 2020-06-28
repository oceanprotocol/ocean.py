import sys

from src.ocean_lib import Ocean
from src.spool_py import SFactory, SPool, BToken, bconstants
from src.util import util
from src.util.util import ETHtoBase, OCEANtoBase, DTtoBase, BPTtoBase, \
    fromBase18, toBase18

def test1(network, OCEAN_address,
          alice_private_key, alice_context, alice_view, alice_config, alice_ocean,
          bob_private_key, bob_context, bob_view, bob_config, bob_ocean):
    print(util.keysStr(alice_private_key, "Alice"))
    print(util.keysStr(bob_private_key, "Bob"))
    
    # Assume Alice and Bob both own OCEAN tokens. Let's check their balances!
    print(alice_view)
    print(bob_view)
    
    #===============================================================
    # 1. Alice publishes a dataset (= publishes a datatoken)
    print("===Step 1: Alice publishes a dataset. Begin.")
    # For now, you're Alice:) Let's proceed.
    alice_DT = alice_ocean.createDataToken('localhost:8030')
    DT_address = alice_DT.getAddress()

    print(f"DT_address = {DT_address}")
    alice_view.DT_address = DT_address #so that the view sees DT info
    bob_view.DT_address = DT_address   # ""
    
    print("===Step 1: Alice publishes a dataset. Done.\n")

    #===============================================================
    # 2. Alice hosts the dataset
    print("===Step 2: Alice hosts the dataset. Begin.")
    # Do from console:
    # >> touch /var/mydata/myFolder1/file
    # >> ENV DT="{'0x1234':'/var/mydata/myFolder1'}"
    # >> docker run @oceanprotocol/provider-py -e CONFIG=DT
    print("===Step 2: Alice hosts the dataset. Done.\n")
    
    #===============================================================
    # 3. Alice mints DTs
    print("===Step 3: Alice mints DTs. Begin.")
    alice_DT.mint(1000.0)
    print("===Step 3: Alice mints DTs. Done.\n")
    print(alice_view)
    
    #===============================================================
    # 4. Alice creates an OCEAN-DT pool (=a Balancer Pool)
    print("===Step 4:  Alice creates an OCEAN-DT pool. Begin.")

    sfactory = SFactory.SFactory(alice_context)
    pool_address = sfactory.newSPool(alice_context.address)
    alice_pool = SPool.SPool(alice_context, pool_address)

    alice_pool.setPublicSwap(True)

    alice_pool.setSwapFee(ETHtoBase(0.1)) #set 10% fee
    
    BToken.BToken(alice_context, DT_address).approve(pool_address, DTtoBase(90.0))
    alice_pool.bind(DT_address, DTtoBase(90.0), bconstants.INIT_WEIGHT_DT)
    
    BToken.BToken(alice_context, OCEAN_address).approve(pool_address, OCEANtoBase(10.0))
    alice_pool.bind(OCEAN_address, OCEANtoBase(10.0), bconstants.INIT_WEIGHT_OCEAN)

    print("===Step 4:  Alice creates an OCEAN-DT pool. Done.\n")
    
    alice_view.pool_address = pool_address #so view sees BPT info
    bob_view.pool_address = pool_address   
    print(alice_view)
    print("alice_pool: " + str(alice_pool))

    #===============================================================
    # 5. Alice adds liquidity to pool
    print("===Step 5: Alice adds liquidity to pool. Begin.")

    BToken.BToken(alice_context, DT_address).approve(pool_address, DTtoBase(9.0))
    alice_pool.rebind(DT_address, DTtoBase(90.0+9.0), bconstants.INIT_WEIGHT_DT)
    
    BToken.BToken(alice_context, OCEAN_address).approve(pool_address, OCEANtoBase(1.0))
    alice_pool.rebind(OCEAN_address, OCEANtoBase(10.0+1.0), bconstants.INIT_WEIGHT_OCEAN)

    print("===Step 5: Alice adds liquidity to pool. Done.\n")
    print(alice_view)
    print("alice_pool: " + str(alice_pool))
    
    # 6. Bob buys a DT from pool
    print("===Step 6: Bob buys a data token from pool. Begin.")
    #bob_pool.buyDataTokens(num_DT=1.0, max_num_OCEAN=2.0)
    print("----before Bob buys----")
    print("alice_pool: " + str(alice_pool))
    
    bob_pool = SPool.SPool(bob_context, pool_address)
    BToken.BToken(bob_context, OCEAN_address).approve(pool_address, OCEANtoBase(2.0))
    bob_pool.swapExactAmountOut(
        tokenIn_address = OCEAN_address,
        maxAmountIn_base = OCEANtoBase(2.0),
        tokenOut_address = DT_address,
        tokenAmountOut_base = DTtoBase(1.0),         
        maxPrice_base = 2 ** 255,
    )
    print("----after Bob buys----")
    print("alice_pool: " + str(alice_pool))
    print("===Step 6: Bob buys 1.0 DTs from pool. Done.\n")
    print(bob_view)
    print("bob_pool: " + str(bob_pool))
    
    #===============================================================
    # 7. Bob consumes dataset
    print("===Step 7: Bob consumes dataset. Begin.")
    bob_DT = bob_ocean.getToken(DT_address)
    _file = bob_DT.download()
    print("===Step 7: Bob consumes dataset. Done.\n")
    print(bob_view)
    
    #===============================================================
    # 8. Alice removes liquidity
    print("===Step 8: Alice removes liquidity. Begin.")
    alice_pool.rebind(DT_address, DTtoBase(90.0+9.0-2.0), bconstants.INIT_WEIGHT_DT)
    alice_pool.rebind(OCEAN_address, OCEANtoBase(10.0+1.0-3.0), bconstants.INIT_WEIGHT_OCEAN)
    print("===Step 8: Alice removes liquidity. Done.\n")
    print(alice_view)
    print("alice_pool: " + str(alice_pool))
    
    #===============================================================
    # 9. Alice sells data tokens
    print("===Step 9: Alice sells tokens. Begin.")
    #alice_pool.sellDataTokens(1.0, min_num_OCEAN=0.0001)
    BToken.BToken(alice_context, DT_address).approve(pool_address, DTtoBase(1.0))
    alice_pool.swapExactAmountIn(
        tokenIn_address = DT_address,
        tokenAmountIn_base = DTtoBase(1.0),
        tokenOut_address = OCEAN_address,
        minAmountOut_base = OCEANtoBase(0.0001),
        maxPrice_base = 2 ** 255,
    )
    print("===Step 9: Alice sells data tokens. Done.\n") 
    print(alice_view)
    print("alice_pool: " + str(alice_pool))   
    
    #===============================================================
    # 10. Alice finalizes pool. Now others can add liquidity.
    print("===Step 10: Alice finalizes pool. Begin.")
    alice_pool.finalize()
    print("===Step 10: Alice finalizes pool. Done.\n")
    
    #===============================================================
    # 11. Bob adds liquidity
    print("===Step 11: Bob adds liquidity. Begin.")
    #bob_pool.addLiquidity_Finalized(
    #    num_BPT=0.1, max_num_DT=1.0, max_num_OCEAN=1.0)
    BToken.BToken(bob_context, DT_address).approve(pool_address, DTtoBase(1.0))
    BToken.BToken(bob_context, OCEAN_address).approve(pool_address, OCEANtoBase(1.0))
    bob_pool.joinPool(BPTtoBase(0.1), [DTtoBase(1.0), OCEANtoBase(1.0)])
    print("===Step 11: Bob adds liquidity. Done.\n")
    print(bob_view)
    print("bob_pool: " + str(bob_pool))
    
    #===============================================================
    # 12. Bob adds liquidity AGAIN
    print("===Step 12: Bob adds liquidity AGAIN. Begin.")
    BToken.BToken(bob_context, DT_address).approve(pool_address, DTtoBase(1.0))
    BToken.BToken(bob_context, OCEAN_address).approve(pool_address, OCEANtoBase(1.0))
    bob_pool.joinPool(BPTtoBase(0.1), [DTtoBase(1.0), OCEANtoBase(1.0)])
    print("===Step 12: Bob adds liquidity AGAIN. Done.\n")
    print(bob_view)
    print("bob_pool: " + str(bob_pool))

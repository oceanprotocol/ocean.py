import sys

from ocean_lib import Ocean
from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.spool import SPool
from ocean_lib.models.btoken import BToken
from ocean_lib.models import bconstants
from ocean_lib.ocean import util
from ocean_lib.ocean.util import toBase18

def test1(network, OCEAN_address,
          alice_ocean, alice_wallet, alice_address,
          bob_ocean, bob_wallet):
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
    pool = alice_ocean.create_pool(
        DT_address, num_DT_base=toBase18(90.0), num_OCEAN_base=toBase18(10.0),
        from_wallet=alice_wallet)
    
    #===============================================================
    # 5. Alice adds liquidity to pool
    pool.addLiquidity(num_DT_base=toBase18(9.0), num_OCEAN_base=toBase18(1.0),
                      from_wallet=alice_wallet)
    
    # 6. Bob buys a DT from pool
    pool = bob_ocean.getPool(pool_address)
    DT_price = fromBase18(pool.getDTSpotPrice_base()) #price of DT, in OCEAN
    pool.buyDataTokens(num_DT_base=toBase18(1.0),
                       max_num_OCEAN_base=toBase18(2.0),
                       from_wallet=bob_wallet)
    
    #===============================================================
    # 7. Bob consumes dataset
    # <don't need to show here>
    
    #===============================================================
    # 8. Alice removes liquidity
    pool.removeLiquidity(num_DT_base=toBase18(2.0),
                         num_OCEAN_base=toBase18(3.0),
                         from_wallet=alice_wallet)
    
    #===============================================================
    # 9. Alice sells data tokens
    pool.sellDataTokens(num_DT_base=toBase18(1.0),
                        min_num_OCEAN_base=toBase18(0.0001),
                        from_wallet=alice_wallet)
    
    #===============================================================
    # 10. Alice finalizes pool. Now others can add liquidity.
    pool.finalize(from_wallet=alice_wallet)
    
    #===============================================================
    # 11. Bob adds liquidity
    pool.addLiquidity_Finalized(
        num_BPT_base=toBase18(0.1), max_num_DT_base=toBase18(1.0),
        max_num_OCEAN_base=toBase18(1.0),
        from_wallet=bob_wallet)
    
    #===============================================================
    # 12. Bob adds liquidity AGAIN
    pool.addLiquidity_Finalized(
        num_BPT_base=toBase18(0.1), max_num_DT_base=toBase18(1.0),
        max_num_OCEAN_base=toBase18(1.0),
        from_wallet=bob_wallet)

from ocean_lib.ocean import util
from ocean_lib.spool_py import SFactory, SPool
    
def test1(network, alice_wallet):
    web3 = alice_wallet.web3
    sfactory_address = util.confFileValue(network, 'SFACTORY_ADDRESS')
    sfactory = SFactory.SFactory(web3, sfactory_address)

    pool_address = sfactory.newSPool(from_wallet=alice_wallet)
    pool = SPool.SPool(web3, pool_address)
    assert isinstance(pool, SPool.SPool)
    

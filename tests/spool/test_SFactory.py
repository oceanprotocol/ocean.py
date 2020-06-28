from ocean_lib.spool_py import SFactory, SPool
    
def test1(alice_address, alice_context):
    sfactory = SFactory.SFactory(alice_context)
    address = sfactory.newSPool(alice_address)
    pool = SPool.SPool(alice_context, address)
    assert isinstance(pool, SPool.SPool)
    

from ocean_lib.ocean import util
from ocean_lib.models.datatoken import DataToken
from ocean_lib.models.dtfactory import DTFactory
    
def test1(network, alice_wallet, dtfactory_address):
    web3 = alice_wallet.web3
    dtfactory = DTFactory(web3, dtfactory_address)

    dt_address = dtfactory.createToken('foo_blob', from_wallet=alice_wallet)
    dt = DataToken(web3, dt_address)
    assert isinstance(dt, DataToken)
    assert dt.blob() == 'foo_blob'
    

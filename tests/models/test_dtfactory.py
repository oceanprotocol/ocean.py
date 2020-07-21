from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dt_factory import DTFactory


def test1(network, alice_wallet, dtfactory_address):
    dtfactory = DTFactory(dtfactory_address)

    dt_address = dtfactory.createToken('foo_blob', from_wallet=alice_wallet)
    dt = DataToken(dtfactory.get_token_address(dt_address))
    assert isinstance(dt, DataToken)
    assert dt.blob() == 'foo_blob'

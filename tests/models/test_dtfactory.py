from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.util import to_base_18


def test1(network, alice_wallet, dtfactory_address):
    dtfactory = DTFactory(dtfactory_address)

    dt_address = dtfactory.createToken(
        "foo_blob", "DT1", "DT1", to_base_18(1000), from_wallet=alice_wallet
    )
    dt = DataToken(dtfactory.get_token_address(dt_address))
    assert isinstance(dt, DataToken)
    assert dt.blob() == "foo_blob"

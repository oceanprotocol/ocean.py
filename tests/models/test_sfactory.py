from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.util import get_sfactory_address


def test1(network, alice_wallet):
    sfactory_address = get_sfactory_address(network)
    sfactory = SFactory(sfactory_address)

    pool_address = sfactory.newBPool(from_wallet=alice_wallet)
    pool = BPool(pool_address)
    assert isinstance(pool, BPool)

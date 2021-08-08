#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.util import get_bfactory_address


def test_bpool_creation(web3, config, alice_wallet):
    """Test the creation of a Balancer Pool from BFactory (happy flow)."""
    bfactory_address = get_bfactory_address(config.address_file, web3=web3)
    bfactory = BFactory(web3, bfactory_address)

    pool_address = bfactory.newBPool(from_wallet=alice_wallet)
    pool = BPool(web3, pool_address)
    assert isinstance(pool, BPool)

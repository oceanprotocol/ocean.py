#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean.util import get_bfactory_address


def test1(network, alice_wallet):
    bfactory_address = get_bfactory_address(network)
    bfactory = BFactory(bfactory_address)

    pool_address = bfactory.newBPool(from_wallet=alice_wallet)
    pool = BPool(pool_address)
    assert isinstance(pool, BPool)

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.v4.factory_router import FactoryRouter
from tests.resources.helper_functions import (
    get_factory_deployer_wallet,
    get_address_of_type,
)

_NETWORK = "ganache"


def test_ocean_tokens_mapping(web3, config, factory_router):
    factory_router = FactoryRouter(web3, factory_router)
    ocean_tokens = factory_router.ocean_tokens(get_address_of_type(config, "Ocean"))
    assert ocean_tokens is True


def test_add_ocean_token(web3, factory_router):
    new_ocean_address = web3.toChecksumAddress(
        "0x967da4048cd07ab37855c090aaf366e4ce1b9f48"
    )
    deployer_wallet = get_factory_deployer_wallet(_NETWORK)
    factory_router = FactoryRouter(web3, factory_router)
    new_router_address = factory_router.router_owner()
    assert new_router_address == deployer_wallet.address
    factory_router_v2 = FactoryRouter(web3, deployer_wallet.address)
    factory_router_v2.add_ocean_token(new_ocean_address, deployer_wallet)

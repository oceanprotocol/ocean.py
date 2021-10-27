#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_contracts_addresses

_NETWORK = "development"


def get_factory_router_address(config):
    """Helper function to retrieve a known factory router address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)["v4"]

    return addresses.get("Router")


def get_ocean_address():
    """Helper function to retrieve a known Ocean address."""
    # FIXME: the Ocean address is the OPF one, need fix from deploy-script.js
    # return addresses.get('Ocean')
    return "0x967da4048cD07aB37855c090aAF366e4ce1b9F48"


def test_ocean_tokens_mapping(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    ocean_tokens = factory_router.ocean_tokens(get_ocean_address())
    assert ocean_tokens is True

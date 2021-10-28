#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.v4.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_contracts_addresses
from tests.resources.helper_functions import get_factory_deployer_wallet

_NETWORK = "ganache"


def get_factory_router_address(config):
    """Helper function to retrieve a known factory router address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses.get("Router")


def get_ocean_address(config):
    """Helper function to retrieve a known Ocean address."""

    addresses = get_contracts_addresses(config.address_file, _NETWORK)
    return addresses.get("Ocean")


def test_ocean_tokens_mapping(web3, config):
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    ocean_tokens = factory_router.ocean_tokens(get_ocean_address(config))
    assert ocean_tokens is True


def test_add_ocean_token(web3, config):
    new_ocean_address = web3.toChecksumAddress(
        "0x967da4048cd07ab37855c090aaf366e4ce1b9f48"
    )
    deployer_wallet = get_factory_deployer_wallet(_NETWORK)
    factory_router = FactoryRouter(web3, get_factory_router_address(config))
    new_router_address = factory_router.router_owner()
    assert new_router_address == deployer_wallet.address
    factory_router_v2 = FactoryRouter(web3, deployer_wallet.address)
    factory_router_v2.add_ocean_token(new_ocean_address, deployer_wallet)

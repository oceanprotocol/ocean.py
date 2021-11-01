#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Address retrieval functions"""
from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.ocean.util import get_contracts_addresses

_NETWORK = "ganache"


def get_nft_factory_address(config):
    """Helper function to retrieve a known ERC721 factory address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[ERC721FactoryContract.CONTRACT_NAME]


def get_nft_template_address(config):
    """Helper function to retrieve a known ERC721 template address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[ERC721Token.CONTRACT_NAME]["1"]


def get_erc20_template_address(config):
    """Helper function to retrieve a known ERC20 template address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[ERC20Token.CONTRACT_NAME]["1"]


def get_mock_dai_contract(config):
    """Helper function to retrieve a known ERC20 template address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses["MockDAI"]


def get_factory_router_address(config):
    """Helper function to retrieve a known factory router address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses["Router"]


def get_ocean_address(config):
    """Helper function to retrieve a known Ocean address."""

    addresses = get_contracts_addresses(config.address_file, _NETWORK)
    return addresses["Ocean"]


def get_ss_address(config):
    """Helper function to retrieve a known Side Staking contract address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses["Staking"]


def get_pool_template_address(config):
    """Helper function to retrieve a known pool template address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses["poolTemplate"]


def get_fixed_rate_address(config):
    """Helper function to retrieve a known Fixed Rate Exchange address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses["FixedPrice"]


def get_dispenser_address(config):
    """Helper function to retrieve a known Dispenser address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[DispenserV4.CONTRACT_NAME]

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""
This module holds following default values for Gas price, Gas limit and more.

"""

ENV_GAS_PRICE = "GAS_PRICE"
ENV_MAX_GAS_PRICE = "MAX_GAS_PRICE"

GAS_LIMIT_DEFAULT = 1000000
MIN_GAS_PRICE = 1000000000

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
ERC721_FACTORY_ADDRESS = "0xe749E2f8482810b11B838Ae8c5eb69e54d610411"
ERC721_TEMPLATE = "0x9C2a015129969c98E9A5BcBEb61A5F907FF5b629"
OCEAN_ADDRESS_V4 = "0x2473f4F7bf40ed9310838edFCA6262C17A59DF64"
SIDE_STAKING_ADDRESS = "0xBb0911124E680D65358Ac46C5404D4dF01F03e80"
POOL_TEMPLATE_ADDRESS = "0x053aE1FeCdc2f391753E2Bf2AAe301E75CC0aac9"

MAX_UINT256 = 2 ** 256 - 1

MAX_INT256 = 2 ** 255 - 1
MIN_INT256 = 2 ** 255 * -1

DEFAULT_NETWORK_NAME = "ganache"
NETWORK_NAME_MAP = {
    1: "Mainnet",
    3: "Ropsten",
    4: "Rinkeby",
    56: "Binance Smart Chain",
    137: "Polygon",
    1287: "Moonbeam Alpha",
    1337: "Ganache",
}

NETWORK_TIMEOUT_MAP = {
    "mainnet": 10 * 60,
    "ropsten": 10 * 60,
    "rinkeby": 5 * 60,
    "bsc": 10 * 60,
    "polygon": 10 * 60,
    "moonbeamalpha": 60,
    "ganache": 2,
}

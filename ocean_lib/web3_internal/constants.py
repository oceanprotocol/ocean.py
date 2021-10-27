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
ERC721_FACTORY_ADDRESS = "0xfeA10BBb093d7fcb1EDf575Aa7e28d37b9DcFcE9"
ERC721_TEMPLATE = "0xF152cF3c67dFD41a317eAe8fAc0e1e8E98724A13"
OCEAN_ADDRESS_V4 = "0x8930D1F61Defb9CBD652136B4C3D93f19AC35678"
SIDE_STAKING_ADDRESS = "0xEBe77E16736359Bf0F9013F6017242a5971cAE76"
POOL_TEMPLATE_ADDRESS = "0xFe0145Caf0EC55D23dc1b08431b071f6e1123a76"

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

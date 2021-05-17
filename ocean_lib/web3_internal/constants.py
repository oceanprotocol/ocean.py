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

MAX_UINT256 = 2 ** 256 - 1

MAX_INT256 = 2 ** 255 - 1
MIN_INT256 = 2 ** 255 * -1

DEFAULT_NETWORK_NAME = "ganache"
NETWORK_NAME_MAP = {
    1: "Mainnet",
    2: "Morden",
    3: "Ropsten",
    4: "Rinkeby",
    42: "Kovan",
    100: "xDai",
    137: "Polygon",
}

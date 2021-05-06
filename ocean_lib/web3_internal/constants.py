#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
ENV_GAS_PRICE = "GAS_PRICE"
ENV_MAX_GAS_PRICE = "MAX_GAS_PRICE"

GAS_LIMIT_DEFAULT = 1000000
MIN_GAS_PRICE = 1000000000

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

DEFAULT_NETWORK_NAME = "ganache"
NETWORK_NAME_MAP = {
    1: "Mainnet",
    2: "Morden",
    3: "Ropsten",
    4: "Rinkeby",
    42: "Kovan",
    100: "xDai",
}

NETWORK_TIMEOUT_MAP = {
    "mainnet": 10 * 60,
    "morden": 10 * 60,
    "ropsten": 5 * 60,
    "rinkeby": 5 * 60,
    "kovan": 10 * 60,
    "xdai": 10 * 60,
    "ganache": 2,
}

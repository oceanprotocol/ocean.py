#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from enforce_typing import enforce_types

# Development chainid is from brownie, rest are from chainlist.org
_CHAINID_TO_NETWORK = {
    8996: "development",  # ganache
    1: "mainnet",
    3: "ropsten",
    4: "rinkeby",
    56: "bsc",
    137: "polygon",
    246: "energyweb",
    1287: "moonbase",
    1285: "moonriver",
    80001: "mumbai",
}
_NETWORK_TO_CHAINID = {
    network: chainID for chainID, network in _CHAINID_TO_NETWORK.items()
}


@enforce_types
def chainIdToNetwork(chainID: int) -> str:
    """Returns the network name for a given chainID"""
    return _CHAINID_TO_NETWORK[chainID]


@enforce_types
def networkToChainId(network: str) -> int:
    """Returns the chainID for a given network name"""
    return _NETWORK_TO_CHAINID[network]

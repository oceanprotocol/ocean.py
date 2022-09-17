#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from enforce_typing import enforce_types

from ocean_lib.ocean import networkutil

@enforce_types
def test_chainIdToNetwork():
    assert networkutil.chainIdToNetwork(8996) == "development"
    assert networkutil.chainIdToNetwork(1) == "mainnet"
    assert networkutil.chainIdToNetwork(137) == "polygon"
    assert networkutil.chainIdToNetwork(80001) == "mumbai"


@enforce_types
def test_networkToChainId():
    assert networkutil.networkToChainId("development") == 8996
    assert networkutil.networkToChainId("mainnet") == 1
    assert networkutil.networkToChainId("polygon") == 137
    assert networkutil.networkToChainId("mumbai") == 80001

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.web3_internal.web3_provider import Web3Provider
from web3.main import Web3


def test_main(dtfactory_address):
    with pytest.raises(AssertionError):
        Web3Provider.init_web3(None, None)

    Web3Provider.set_web3(None)
    assert Web3Provider._web3 is None
    assert isinstance(Web3Provider.get_web3(network_url="http://test.test"), Web3)
    assert Web3Provider._web3 is not None

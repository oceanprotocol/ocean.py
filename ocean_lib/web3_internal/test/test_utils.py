#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest

from ocean_lib.web3_internal.utils import (
    generate_multi_value_hash,
    get_chain_id,
    get_network_name,
    prepare_prefixed_hash,
)


@pytest.mark.unit
def test_get_network_name(web3):
    assert get_network_name(1) == "mainnet"
    assert get_network_name(4) == "rinkeby"
    assert get_network_name(3) == "ropsten"
    assert get_network_name(137) == "polygon"
    assert get_network_name(8996) == "ganache"
    assert get_network_name(web3=web3) == "ganache"
    assert get_network_name(-1) == "ganache"
    assert get_network_name() == "ganache"


@pytest.mark.unit
def test_get_chain_id(web3):
    assert get_chain_id(web3) == 8996


@pytest.mark.unit
def test_generate_multi_value_hash(alice_address, alice_private_key):
    with pytest.raises(AssertionError):
        generate_multi_value_hash(["more", "types", "than"], ["values"])

    expected = "0xb0594251e54435c54e9b24ec910288bcd2759e0e4ed0c66248971045c2cab143"
    assert alice_private_key == os.getenv("TEST_PRIVATE_KEY1")
    assert alice_address == "0xA78deb2Fa79463945C247991075E2a0e98Ba7A09"
    tested = generate_multi_value_hash(["address"], [alice_address]).hex()
    assert tested == expected, "The tested address is not the expected one."


@pytest.mark.unit
def test_prepare_fixed_hash():
    expected = "0x5662cc8481d004c9aff44f15f3ed133dd54f9cfba0dbf850f69b1cbfc50145bf"
    assert (
        prepare_prefixed_hash("0x0").hex() == expected
    ), "The address is not the expected one."

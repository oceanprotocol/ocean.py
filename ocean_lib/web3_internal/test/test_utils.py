#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.web3_internal.utils import (
    generate_multi_value_hash,
    prepare_prefixed_hash,
)


def test_generate_multi_value_hash(alice_address):
    with pytest.raises(AssertionError):
        generate_multi_value_hash(["more", "types", "than"], ["values"])

    expected = "0x6d59f15c5814d9fddd2e69d1f6f61edd0718e337c41ec74011900c0d736a9fec"
    assert generate_multi_value_hash(["address"], [alice_address]).hex() == expected


def test_prepare_fixed_hash():
    expected = "0x5662cc8481d004c9aff44f15f3ed133dd54f9cfba0dbf850f69b1cbfc50145bf"
    assert prepare_prefixed_hash("0x0").hex() == expected

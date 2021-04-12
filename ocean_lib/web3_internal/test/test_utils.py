#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from ocean_lib.web3_internal.utils import (
    generate_multi_value_hash,
    prepare_prefixed_hash,
)


def test_generate_multi_value_hash(alice_address, alice_private_key):
    with pytest.raises(AssertionError):
        generate_multi_value_hash(["more", "types", "than"], ["values"])

    expected = "0x7ba270cc76c2dde25e744613ec459be48c8130f6f996b66f8df1b60662f60cea"
    assert alice_private_key == os.getenv("TEST_PRIVATE_KEY1")
    assert alice_address == "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260"
    tested = generate_multi_value_hash(["address"], [alice_address]).hex()
    assert tested == expected


def test_prepare_fixed_hash():
    expected = "0x5662cc8481d004c9aff44f15f3ed133dd54f9cfba0dbf850f69b1cbfc50145bf"
    assert prepare_prefixed_hash("0x0").hex() == expected

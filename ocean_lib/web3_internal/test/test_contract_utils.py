#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from web3.main import Web3

from ocean_lib.web3_internal.contract_utils import _checksum_contract_addresses


def test_checksum_contract_addresses(monkeypatch):
    addresses = {
        "chainId": 7,
        "test": "0x20802d1a9581b94e51db358c09e0818d6bd071b4",
        "dict": {"address": "0xe2dd09d719da89e5a3d0f2549c7e24566e947260"},
    }
    assert Web3.isChecksumAddress(addresses["test"]) is False
    assert Web3.isChecksumAddress(addresses["dict"]["address"]) is False
    checksum_addresses = _checksum_contract_addresses(addresses)
    assert Web3.isChecksumAddress(checksum_addresses["test"]) is True
    assert Web3.isChecksumAddress(addresses["dict"]["address"]) is True

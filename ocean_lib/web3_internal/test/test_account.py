#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import json

from ocean_lib.web3_internal.account import Account
from tests.resources.ddo_helpers import get_resource_path


def test_account_properties_from_file(alice_account):
    key_file = get_resource_path("keys", "key_file_2.json")
    account = Account(key_file=key_file, password="123", address="0x0")
    assert json.loads(account.key)["id"] == "0902d04b-f26e-5c1f-e3ae-78d2c1cb16e7"
    assert account.private_key is None, "The private key can be shown."
    assert account.key == account._encrypted_key
    assert account.key_file == str(key_file)

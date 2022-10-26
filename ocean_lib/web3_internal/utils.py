#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from enforce_typing import enforce_types
from eth_account.account import Account
from eth_keys import keys
from eth_utils import decode_hex

logger = logging.getLogger(__name__)


@enforce_types
def private_key_to_address(private_key: str) -> str:
    return Account.from_key(private_key).address


@enforce_types
def private_key_to_public_key(private_key: str) -> str:
    private_key_bytes = decode_hex(private_key)
    private_key_object = keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key

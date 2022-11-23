#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import random
import string
import time

from brownie.network import accounts, chain, priority_fee


def get_wallets(ocean):
    alice_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY1")
    bob_private_key = os.getenv("REMOTE_TEST_PRIVATE_KEY2")

    instrs = "You must set it. It must hold Mumbai MATIC."
    assert alice_private_key, f"Need envvar REMOTE_TEST_PRIVATE_KEY1. {instrs}"
    assert bob_private_key, f"Need envvar REMOTE_TEST_PRIVATE_KEY2. {instrs}"

    # wallets
    alice_wallet = accounts.add(alice_private_key)
    bob_wallet = accounts.add(bob_private_key)

    print(f"alice_wallet.address = '{alice_wallet.address}'")
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    return (alice_wallet, bob_wallet)


def random_chars() -> str:
    cand_chars = string.ascii_uppercase + string.digits
    s = "".join(random.choices(cand_chars, k=8)) + str(time.time())
    return s


def set_aggressive_gas_fees():
    # Polygon & Mumbai uses EIP-1559. So, dynamically determine priority fee
    priority_fee(chain.priority_fee)

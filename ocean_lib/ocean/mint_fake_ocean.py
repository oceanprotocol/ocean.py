#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.contract_utils import get_addresses_with_fallback, get_web3
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.utils import get_ether_balance
from ocean_lib.web3_internal.wallet import Wallet


def mint_fake_OCEAN(config: dict) -> None:
    """
    Does the following:
    1. Mints tokens
    2. Distributes tokens to TEST_PRIVATE_KEY1 and TEST_PRIVATE_KEY2
    """
    network_addresses = get_addresses_with_fallback(config)

    web3 = get_web3(config["RPC_URL"])
    deployer_wallet = Wallet(
        web3,
        private_key=os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY"),
        block_confirmations=config["BLOCK_CONFIRMATIONS"],
        transaction_timeout=config["TRANSACTION_TIMEOUT"],
    )

    OCEAN_token = Datatoken(web3, address=network_addresses["development"]["Ocean"])
    amt_distribute = to_wei("2000")
    OCEAN_token.mint(
        deployer_wallet.address, to_wei("20000"), from_wallet=deployer_wallet
    )
    for key_label in ["TEST_PRIVATE_KEY1", "TEST_PRIVATE_KEY2", "TEST_PRIVATE_KEY3"]:
        key = os.environ.get(key_label)
        if not key:
            continue

        w = Wallet(
            web3,
            private_key=key,
            block_confirmations=config["BLOCK_CONFIRMATIONS"],
            transaction_timeout=config["TRANSACTION_TIMEOUT"],
        )

        if OCEAN_token.balanceOf(w.address) < amt_distribute:
            OCEAN_token.mint(w.address, amt_distribute, from_wallet=deployer_wallet)

        if get_ether_balance(web3, w.address) < to_wei("2"):
            send_ether(deployer_wallet, w.address, to_wei("4"))

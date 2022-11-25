#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import random
import runpy

from brownie.network import accounts

from . import util


def test_simple_remote_readme(monkeypatch):
    accounts.clear()
    (ref_alice_wallet, _) = util.get_wallets()
    
    # README generation command:
    # mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs
    script = pathlib.Path(
        __file__, "..", "..", "..", "generated-readmes", "test_simple-remote.py"
    )
    
    result = runpy.run_path(str(script), run_name="__main__")
    ocean = result["ocean"]
    alice_wallet = result["alice_wallet"]

    #at this point, this script should have set up ocean and the wallets

    #make sure that the script used REMOTE_TEST_PRIVATE_KEY1 wallet, like reference wallet
    assert alice_wallet.address == ref_alice_wallet.address

    # ensure we pay enough
    util.set_aggressive_gas_fees()

    #besides what the readme script does, is it actually able to do more?
    util.do_ocean_tx_and_handle_gotchas(ocean, alice_wallet)

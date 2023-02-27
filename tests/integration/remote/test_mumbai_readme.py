#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

from brownie.network import accounts

from . import util


def test_simple_remote_readme(monkeypatch):
    monkeypatch.delenv("ADDRESS_FILE")
    accounts.clear()
    (ref_alice_wallet, _) = util.get_wallets()

    # README generation command:
    # mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs
    script = pathlib.Path(
        __file__, "..", "..", "..", "generated-readmes", "test_setup-remote.py"
    )

    try:
        result = runpy.run_path(str(script), run_name="__main__")
    except AssertionError as e:  # skip if zero funds in account
        if "Alice needs MATIC" in str(e) or "Bob needs MATIC" in str(e):
            return
        raise (e)
    ocean = result["ocean"]
    alice = result["alice"]

    # at this point, this script should have set up ocean and the wallets

    # make sure that the script used REMOTE_TEST_PRIVATE_KEY1 wallet, like reference wallet
    assert alice.address == ref_alice_wallet.address

    # besides what the readme script does, is it actually able to do more?
    util.do_ocean_tx_and_handle_gotchas(ocean, alice)

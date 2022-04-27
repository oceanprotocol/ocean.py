#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

import pytest

scripts = pathlib.Path(__file__, "..", "generated-readmes").resolve().glob("*.py")


@pytest.mark.parametrize("script", scripts)
def test_script_execution(script, monkeypatch):
    # mkcodes --github --output tests/generated-readmes/test_{name}.py READMEs
    if "developers" in script.name or "datatokens-flow" in script.name:
        # developers flow does not contain Python snippets, but mostly console
        # and samples; it should be skipped
        # datatokens-flow is skipped because it is run as a prerequisite
        return

    if "c2d-flow-more" in script.name:
        # TODO: this SHOULD stay in the readme flow
        return

    if "parameters" in script.name:
        # needs some env vars set to run
        monkeypatch.setenv("METADATA_CACHE_URI", "http://172.15.0.5:5000")
        monkeypatch.setenv("PROVIDER_URL", "http://172.15.0.4:8030")

    runs_with_prerequisites = [
        "c2d-flow",
        "datatokens-flow",
        "dispenser-flow",
        "erc20-enterprise",
        "fixed-rate-exchange-flow",
        "marketplace-flow",
    ]

    globs = {}
    for item in runs_with_prerequisites:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__, "..", "generated-readmes/test_datatokens-flow.py"
            )
            result = runpy.run_path(str(prerequisite), run_name="__main__")
            for key in [
                "os",
                "Wallet",
                "config",
                "ocean",
                "alice_wallet",
                "erc721_nft",
                "erc20_token",
            ]:
                globs[key] = result[key]

    runpy.run_path(str(script), run_name="__main__", init_globals=globs)

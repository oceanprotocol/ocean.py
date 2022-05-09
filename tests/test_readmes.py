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
    # README generation command:
    # mkcodes --github --output tests/generated-readmes/test_{name}.py READMEs

    if (
        "developers" in script.name
        or "datatokens-flow" in script.name
        or "c2d-flow-more-examples" in script.name
    ):
        # developers.md skipped because it does not have end-to-end Python snippets, just console
        # datatokens-flow.md skipped because it is run as a prerequisite for the others, so it is tested implicitly
        # c2d-flow-more-examples skipped because it can not be parsed separately from c2d-flow
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
        "consume-flow",
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

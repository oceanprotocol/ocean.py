#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

import pytest

scripts = pathlib.Path(__file__, "..", "generated-readmes").resolve().glob("*.py")


@pytest.mark.parametrize("script", scripts)
def test_script_execution(script):
    # mkcodes --github --output tests/generated-readmes/test_{name}.py READMEs
    if "c2d-flow.py" not in script.name:
        # TODO: remove
        return

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
            result = runpy.run_path(prerequisite, run_name="__main__")
            for key in ["config", "ocean", "alice_wallet", "erc721_nft", "erc20_token"]:
                globs[key] = result[key]

    runpy.run_path(script, run_name="__main__", init_globals=globs)

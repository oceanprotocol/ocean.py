#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

import pytest

# This file tests READMEs on local chain (ganache).
# For tests of READMEs on remote chains, see tests/integration/remote/

scripts = pathlib.Path(__file__, "..", "..", "generated-readmes").resolve().glob("*.py")


@pytest.mark.parametrize("script", scripts)
def test_script_execution(script):
    # README generation command:
    # mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs

    skippable = [
        "c2d-flow-more-examples",
        "developers",
        "df",
        "install",
        "parameters",
        "predict-eth",
        "services",
        "setup-local",
        "setup-remote",
        "publish-flow-restapi",  # TODO: fix and restore
    ]

    if script.name.replace("test_", "").replace(".py", "") in skippable:
        return

    runs_with_local_setup = [
        "profile-nfts-flow",
        "key-value-flow",
        "search-and-filter-assets",
        "main-flow",
        "c2d-flow",
        "publish-flow-graphql",
        "publish-flow-onchain",
    ]

    globs = {}
    for item in runs_with_local_setup:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__,
                "..",
                "..",
                "generated-readmes/test_setup-local.py",
            )
            result = runpy.run_path(str(prerequisite), run_name="__main__")
            for key in [
                "os",
                "config",
                "ocean",
                "alice",
                "bob",
            ]:
                globs[key] = result[key]

    runpy.run_path(str(script), run_name="__main__", init_globals=globs)

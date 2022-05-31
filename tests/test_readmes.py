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
    # mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs

    if (
        "developers" in script.name
        or "publish-flow" in script.name
        or "data-nfts-and-datatokens-flow" in script.name
        or "c2d-flow-more-examples" in script.name
    ):
        # developers.md skipped because it does not have end-to-end Python snippets, just console
        # data-nfts-and-datatokens-flow.md and publish-flow skipped because it they run as prerequisites for the others, so they are tested implicitly
        # c2d-flow-more-examples skipped because it can not be parsed separately from c2d-flow
        return

    if "parameters" in script.name:
        # needs some env vars set to run
        monkeypatch.setenv("METADATA_CACHE_URI", "http://172.15.0.5:5000")
        monkeypatch.setenv("PROVIDER_URL", "http://172.15.0.4:8030")

    runs_with_prerequisites = [
        "c2d-flow",
        "dispenser-flow",
        "datatoken-enterprise",
        "fixed-rate-exchange-flow",
        "marketplace-flow",
        "key-value-flow",
        "profile-nfts-flow",
        "consume-flow",
    ]

    globs = {}
    for item in runs_with_prerequisites:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__,
                "..",
                "generated-readmes/test_data-nfts-and-datatokens-flow.py",
            )
            result = runpy.run_path(str(prerequisite), run_name="__main__")
            for key in [
                "os",
                "Wallet",
                "config",
                "ocean",
                "alice_wallet",
                "data_nft",
                "datatoken",
            ]:
                globs[key] = result[key]

    runs_with_publish = [
        "marketplace-flow",
        "consume-flow",
        "datatoken-enterprise",
    ]
    for item in runs_with_publish:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__,
                "..",
                "generated-readmes/test_publish-flow.py",
            )
            result = runpy.run_path(
                str(prerequisite), run_name="__main__", init_globals=globs
            )
            for key in [
                "asset",
                "ZERO_ADDRESS",
                "did",
                "metadata",
                "encrypted_files",
            ]:
                globs[key] = result[key]

    runpy.run_path(str(script), run_name="__main__", init_globals=globs)

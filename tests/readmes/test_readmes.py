#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

import pytest

scripts = pathlib.Path(__file__, "..", "..", "generated-readmes").resolve().glob("*.py")


@pytest.mark.parametrize("script", scripts)
def test_script_execution(script, monkeypatch):
    # README generation command:
    # mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs

    if (
        "developers" in script.name
        or "df" in script.name
        or "publish-flow" in script.name
        or "data-nfts-and-datatokens-flow" in script.name
        or "c2d-flow-more-examples" in script.name
        or "parameters" in script.name
    ):
        # developers.md skipped because it does not have end-to-end Python snippets, just console
        # df.md -- ditto
        # data-nfts-and-datatokens-flow.md and publish-flow skipped because it they run as prerequisites for the others, so they are tested implicitly
        # c2d-flow-more-examples skipped because it can not be parsed separately from c2d-flow
        return

    if (
        "predict-eth" in script.name
        or "simple-remote" in script.name
        or "c2d-flow" in script.name
    ):
        # TODO: implement remote flows readme tests
        # C2D FLOW IS NOW REMOTE. Can we have a local one?
        return

    runs_with_prerequisites = [
        "c2d-flow",
        "dispenser-flow",
        "datatoken-enterprise",
        "marketplace-flow",
        "key-value-flow",
        "profile-nfts-flow",
        "consume-flow",
        "search-and-filter-assets",
    ]

    globs = {}
    for item in runs_with_prerequisites:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__,
                "..",
                "..",
                "generated-readmes/test_data-nfts-and-datatokens-flow.py",
            )
            result = runpy.run_path(str(prerequisite), run_name="__main__")
            for key in [
                "os",
                "config",
                "ocean",
                "alice_wallet",
                "bob_wallet",
                "data_nft",
                "datatoken",
            ]:
                globs[key] = result[key]

    runs_with_publish = [
        "consume-flow",
        "datatoken-enterprise",
    ]
    for item in runs_with_publish:
        if item in script.name:
            prerequisite = pathlib.Path(
                __file__,
                "..",
                "..",
                "generated-readmes/test_publish-flow.py",
            )
            result = runpy.run_path(
                str(prerequisite), run_name="__main__", init_globals=globs
            )
            for key in [
                "asset",
                "ddo",
                "ZERO_ADDRESS",
                # "did",
                "metadata",
                "url_file",
            ]:
                globs[key] = result[key]

    runpy.run_path(str(script), run_name="__main__", init_globals=globs)


def test_simple_remote(monkeypatch):
    script = pathlib.Path(
        __file__, "..", "..", "generated-readmes", "test_simple-remote.py"
    )
    result = runpy.run_path(str(script), run_name="__main__")
    ocean, alice_wallet = result["ocean"], result["alice_wallet"]
    data_nft = ocean.create_data_nft("NFT1", "NFT1", alice_wallet)
    assert data_nft
    datatoken = data_nft.create_datatoken(
        "Datatoken 1", "DT1", from_wallet=alice_wallet
    )
    assert datatoken

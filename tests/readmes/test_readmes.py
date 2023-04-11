#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pathlib
import runpy

import pytest

# This file tests READMEs on local chain (ganache).
# For tests of READMEs on remote chains, see tests/integration/remote/

scripts = pathlib.Path(__file__, "..", "..", "generated-readmes").resolve().glob("*.py")
script_names = [script.name for script in scripts if script.name != "__init__.py"]


class TestReadmes(object):
    @classmethod
    def setup_class(self):
        globs = {}
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

        self.globs = globs

    @pytest.mark.parametrize("script_name", script_names)
    def test_script_execution(self, script_name):
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
            "gas-strategy-remote",
        ]

        if script_name.replace("test_", "").replace(".py", "") in skippable:
            return

        script = pathlib.Path(__file__, "..", "..", "generated-readmes", script_name)
        runpy.run_path(str(script), run_name="__main__", init_globals=self.globs)

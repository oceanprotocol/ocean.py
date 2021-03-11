#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.config_provider import ConfigProvider


def test_set_config():
    """Tests that a custom config can be set on the ConfigProvider."""
    config = "foo config"
    ConfigProvider.set_config(config)

    assert ConfigProvider.get_config() == "foo config"

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from enforce_typing import enforce_types
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.example_config import ExampleConfig

def enforce_types2(func):
    config = ConfigProvider.peek_config()
    if config is not None and config["util"].getboolean("typecheck"):
        return func
    elif not ExampleConfig.get_config()["util"].getboolean("typecheck"):
        return func
    else:
        return enforce_types(func)

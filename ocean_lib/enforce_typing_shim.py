#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from enforce_typing import enforce_types
from ocean_lib.config import Config
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean.env_constants import ENV_CONFIG_FILE


def setup_enforce_typing_shim():
    ConfigProvider.set_config(Config(os.getenv(ENV_CONFIG_FILE)))


def enforce_types_shim(func):
    if not ConfigProvider.get_config()["util"].getboolean("typecheck"):
        return func
    return enforce_types(func)

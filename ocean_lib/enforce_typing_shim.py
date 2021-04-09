#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import distutils.util
import os

from enforce_typing import enforce_types
from ocean_lib.config import Config, config_defaults, NAME_TYPECHECK
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean.env_constants import ENV_CONFIG_FILE


def setup_enforce_typing_shim():
    ConfigProvider.set_config(Config(os.getenv(ENV_CONFIG_FILE)))


def enforce_types_shim(func):
    try:
        c = ConfigProvider.get_config()
    except AssertionError:  # handle if ConfigProvider.set_config() not done yet
        c = config_defaults

    val = c["util"][NAME_TYPECHECK]
    typecheck = distutils.util.strtobool(val)

    if typecheck:
        return enforce_types(func)
    return func

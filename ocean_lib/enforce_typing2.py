#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from enforce_typing import enforce_types
from ocean_lib.config_provider import ConfigProvider

def enforce_types(func):
    if not ConfigProvider.get_config()["util"].getboolean("typecheck"):
        return func
    else:
        return enforce_types(func)

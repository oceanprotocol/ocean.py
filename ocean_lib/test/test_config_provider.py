#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.config_provider import ConfigProvider

def test1():
    config = "foo config"
    ConfigProvider.set_config(config)
    
    assert ConfigProvider.get_config() == "foo config"

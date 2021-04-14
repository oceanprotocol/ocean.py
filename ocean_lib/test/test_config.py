#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.config import Config


def test_metadata_cache_url_property():
    config = Config()
    metadata_cache_url = config.metadata_cache_url
    assert metadata_cache_url
    assert metadata_cache_url == config.metadata_store_url
    assert metadata_cache_url == config.aquarius_url

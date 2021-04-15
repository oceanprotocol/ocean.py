#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.config import Config


def test_metadata_cache_uri_property():
    """Tests if the URL of the aquarius matches 'metadata_cache_uri' property."""
    config = Config()
    metadata_cache_uri = config.metadata_cache_uri
    assert metadata_cache_uri
    assert metadata_cache_uri.startswith("https://aquarius")
    assert metadata_cache_uri == "https://aquarius.marketplace.oceanprotocol.com"

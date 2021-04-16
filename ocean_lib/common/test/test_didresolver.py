#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
from datetime import datetime

from ocean_lib.common.ddo.ddo import DDO
from ocean_lib.common.did import DID
from ocean_lib.common.did_resolver.did_resolver import DIDResolver
from tests.resources.ddo_helpers import get_resource_path

logger = logging.getLogger()


class DataToken:
    def __init__(self, token_address):
        self._token_address = token_address

    def get_metadata_url(self):
        return "http://localhost:5000"


# TODO: repurpose/refurbish
def not_test_did_resolver_library(publisher_account, aquarius):
    did_resolver = DIDResolver(DataToken)

    sample_ddo_path = get_resource_path("ddo", "ddo_sample1.json")
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)
    asset1 = DDO(json_filename=sample_ddo_path)
    asset1._did = DID.did({"0": f"0x{datetime.now().timestamp()}"})
    aquarius.publish_asset_ddo(asset1)

    did_resolved = did_resolver.resolve_asset(asset1.did, token_address="010")
    assert did_resolved
    assert did_resolved.did == asset1.did

    try:
        aquarius.retire_asset_ddo(asset1.did)
    except Exception:
        pass

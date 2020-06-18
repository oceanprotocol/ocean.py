#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os

from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.ddo.ddo import DDO

from tests.resources.helper_functions import (get_consumer_account, get_publisher_account,
                                              get_registered_ddo)


def test_market_flow(consumer_ocean_instance, publisher_ocean_instance):
    pub_acc = get_publisher_account()

    # Register ddo
    ddo = get_registered_ddo(publisher_ocean_instance, pub_acc)
    assert isinstance(ddo, DDO)
    assert ddo._other_values['dataTokenAddress']

    cons_ocn = consumer_ocean_instance
    consumer_account = get_consumer_account()
    config = cons_ocn.config

    downloads_path_elements = len(
        os.listdir(config.downloads_path)) if os.path.exists(config.downloads_path) else 0

    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    sa = ServiceAgreement.from_json(service.as_dictionary())

    dt = publisher_ocean_instance.get_data_token(ddo._other_values['dataTokenAddress'])
    dt.mint(pub_acc.address, 100, pub_acc)
    dt.transfer(consumer_account.address, 10, pub_acc)

    assert cons_ocn.assets.download(
        ddo.did,
        sa.index,
        consumer_account,
        config.downloads_path)

    assert len(os.listdir(config.downloads_path)) == downloads_path_elements + 1

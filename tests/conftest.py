#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import uuid

import pytest
from ocean_lib.web3_stuff.contract_handler import ContractHandler
from ocean_lib.web3_stuff.web3_provider import Web3Provider
from ocean_utils.aquarius import AquariusProvider

from examples import ExampleConfig
from ocean_lib.ocean.util import get_web3_provider
from tests.resources.helper_functions import (get_consumer_ocean_instance,
                                              get_metadata, get_publisher_account,
                                              get_publisher_ocean_instance, get_registered_ddo,
                                              setup_logging)

setup_logging()


@pytest.fixture
def setup_all():
    config = ExampleConfig.get_config()
    Web3Provider.init_web3(provider=get_web3_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)


@pytest.fixture
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def registered_ddo():
    ocn = get_publisher_ocean_instance()
    aqua = AquariusProvider.get_aquarius(ocn.config.aquarius_url)
    for did in aqua.list_assets():
        aqua.retire_asset_ddo(did)

    return get_registered_ddo(ocn, get_publisher_account())


@pytest.fixture
def web3_instance():
    config = ExampleConfig.get_config()
    return Web3Provider.get_web3(config.network_url)


@pytest.fixture
def metadata():
    metadata = get_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    return metadata

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.models.metadata import MetadataContract
from ocean_lib.ocean.test.test_ocean_assets import create_asset
from ocean_lib.ocean.util import get_contracts_addresses
from tests.resources.ddo_helpers import wait_for_ddo
from tests.resources.helper_functions import get_publisher_wallet


def test_metadata_contract(publisher_ocean_instance, config):
    ocn = publisher_ocean_instance
    alice = get_publisher_wallet()
    block = ocn.web3.eth.block_number

    ddo_address = get_contracts_addresses(config.address_file, "ganache")[
        MetadataContract.CONTRACT_NAME
    ]
    ddo_registry = MetadataContract(ocn.web3, ddo_address)

    # Tested the event properties.
    assert (
        ddo_registry.event_MetadataCreated.abi["name"]
        == MetadataContract.EVENT_METADATA_CREATED
    )
    assert (
        ddo_registry.event_MetadataUpdated.abi["name"]
        == MetadataContract.EVENT_METADATA_UPDATED
    )

    # Tested get_event_log for create event.
    original_ddo = create_asset(ocn, alice)
    assert original_ddo, "Create asset failed."

    asset_id = original_ddo.asset_id
    creation_log = ddo_registry.get_event_log(
        ddo_registry.EVENT_METADATA_CREATED, block, asset_id, 30
    )
    assert creation_log, "No ddo created event."
    assert creation_log.args.createdBy == alice.address
    assert (
        creation_log.args.createdBy == alice.address
    ), "The event is not created by the publisher."
    assert (
        creation_log.event == ddo_registry.EVENT_METADATA_CREATED
    ), "Different event types."

    # Tested get_event_log for update event.
    ddo = wait_for_ddo(ocn, original_ddo.did)
    _ = ocn.assets.update(ddo, alice)
    updating_log = ddo_registry.get_event_log(
        ddo_registry.EVENT_METADATA_UPDATED, block, asset_id, 30
    )
    assert updating_log, "No ddo updated event."
    assert (
        updating_log.args.updatedBy == alice.address
    ), "The event is not updated by the publisher."
    assert (
        updating_log.event == ddo_registry.EVENT_METADATA_UPDATED
    ), "Different event types."

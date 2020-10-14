#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import time
import uuid

import pytest
from eth_utils import add_0x_prefix

from ocean_lib.models.data_token import DataToken
from ocean_utils.agreements.service_factory import ServiceDescriptor
from ocean_utils.ddo.ddo import DDO
from ocean_utils.did import DID, did_to_id

from tests.resources.helper_functions import (
    get_algorithm_ddo,
    get_computing_metadata,
    get_resource_path,
    get_publisher_wallet, get_consumer_wallet, wait_for_ddo, wait_for_update)


def create_asset(ocean, publisher):
    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(my_secret_store)
    return ocean.assets.create(asset.metadata, publisher, [auth_service])


def test_register_asset(publisher_ocean_instance):
    ocn = publisher_ocean_instance
    ddo_reg = ocn.assets.ddo_registry()
    block = ocn.web3.eth.blockNumber
    alice = get_publisher_wallet()
    bob = get_consumer_wallet()

    def _get_num_assets(_minter):
        dids = [add_0x_prefix(did_to_id(a))
                for a in ocn.assets.owner_assets(_minter)]
        dids = [a for a in dids if len(a) == 42]
        return len([a for a in dids if DataToken(a).contract_concise.isMinter(_minter)])

    num_assets_owned = _get_num_assets(alice.address)

    original_ddo = create_asset(ocn, alice)
    assert original_ddo, f'create asset failed.'

    # try to resolve new asset
    did = original_ddo.did
    asset_id = original_ddo.asset_id
    log = ddo_reg.get_event_log(ddo_reg.EVENT_METADATA_CREATED, block, asset_id, 30)
    assert log, f'no ddo created event.'

    ddo = wait_for_ddo(ocn, did)
    ddo_dict = ddo.as_dictionary()
    original = original_ddo.as_dictionary()
    assert ddo_dict['publicKey'] == original['publicKey']
    assert ddo_dict['authentication'] == original['authentication']
    assert ddo_dict['service']
    assert original['service']
    metadata = ddo_dict['service'][0]['attributes']
    if 'datePublished' in metadata['main']:
        metadata['main'].pop('datePublished')
    assert ddo_dict['service'][0]['attributes']['main']['name'] == \
        original['service'][0]['attributes']['main']['name']
    assert ddo_dict['service'][1] == original['service'][1]

    # Can't resolve unregistered asset
    unregistered_did = DID.did({"0": "0x00112233445566"})
    with pytest.raises(ValueError):
        ocn.assets.resolve(unregistered_did)

    # Raise error on bad did
    invalid_did = "did:op:0123456789"
    with pytest.raises(ValueError):
        ocn.assets.resolve(invalid_did)

    meta_data_assets = ocn.assets.search('')
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    # Publish the metadata
    _ = ddo.metadata['main']['name']
    _name = 'updated name'
    ddo.metadata['main']['name'] = _name
    assert ddo.metadata['main']['name'] == _name
    try:
        ocn.assets.update(ddo, bob)
        assert False, f'this asset update should fail, but did not.'
    except Exception:
        pass

    _ = ocn.assets.update(ddo, alice)
    log = ddo_reg.get_event_log(ddo_reg.EVENT_METADATA_UPDATED, block, asset_id, 30)
    assert log, f'no ddo updated event'
    _asset = wait_for_update(ocn, ddo.did, 'name', _name)
    assert _asset, f'Cannot read asset after update.'
    assert _asset.metadata['main']['name'] == _name, f'updated asset does not have the new updated name !!!'

    assert ocn.assets.owner(ddo.did) == alice.address, f'asset owner does not seem correct.'

    assert _get_num_assets(alice.address) == num_assets_owned + 1


def test_ocean_assets_search(publisher_ocean_instance, metadata):
    publisher = get_publisher_wallet()
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert len(publisher_ocean_instance.assets.search('Monkey')) > 0


def test_ocean_assets_validate(publisher_ocean_instance, metadata):
    assert publisher_ocean_instance.assets.validate(metadata), f'metadata should be valid, unless the schema changed.'


def test_ocean_assets_algorithm(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    metadata = get_algorithm_ddo()['service'][0]
    metadata['attributes']['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata['attributes'], publisher)
    assert ddo
    _ddo = wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert _ddo, f'assets.resolve failed for did {ddo.did}'


def test_ocean_assets_compute(publisher_ocean_instance):
    publisher = get_publisher_wallet()
    metadata = get_computing_metadata()
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    ddo = publisher_ocean_instance.assets.create(metadata, publisher)
    assert ddo
    _ddo = wait_for_ddo(publisher_ocean_instance, ddo.did)
    assert _ddo, f'assets.resolve failed for did {ddo.did}'

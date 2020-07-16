#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os
import time
import uuid

from ocean_utils.agreements.service_factory import ServiceDescriptor
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.ddo.ddo import DDO

from ocean_lib.assets.asset import Asset
from ocean_lib.assets.service_agreement import ServiceAgreement
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from tests.resources.helper_functions import (
    get_consumer_account,
    get_publisher_account,
    get_registered_ddo,
    get_publisher_ocean_instance,
    get_consumer_ocean_instance,
    mint_tokens_and_wait, get_resource_path)


def test_compute_flow():
    ######
    # setup
    pub_acc = get_publisher_account()
    publisher_ocean_instance = get_publisher_ocean_instance()
    consumer_ocean_instance = get_consumer_ocean_instance()
    cons_ocn = consumer_ocean_instance
    consumer_account = get_consumer_account()

    ######
    # Publish Assets

    # Dataset with compute service
    sample_ddo_path = get_resource_path('ddo', 'ddo_with_compute_service.json')
    old_ddo = DDO(json_filename=sample_ddo_path)
    metadata = old_ddo.metadata
    metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())
    service = old_ddo.get_service(ServiceTypes.CLOUD_COMPUTE)
    compute_service = ServiceDescriptor.compute_service_descriptor(
        service.attributes,
        DataServiceProvider.get_compute_endpoint(publisher_ocean_instance.config)
    )
    compute_ddo = publisher_ocean_instance.assets.create(
        metadata,
        pub_acc,
        service_descriptors=[compute_service],
    )
    did = compute_ddo.did
    _compute_ddo = publisher_ocean_instance.assets.resolve(compute_ddo.did)

    # algorithm with download service
    algorithm_ddo_path = get_resource_path('ddo', 'ddo_sample_algorithm.json')
    algo_main = DDO(json_filename=algorithm_ddo_path).metadata['main']
    algo_meta_dict = algo_main['algorithm'].copy()
    algo_meta_dict['url'] = algo_main['files'][0]['url']
    algorithm_meta = AlgorithmMetadata(algo_meta_dict)

    ######
    # Mint tokens for dataset and assign to publisher
    # sa = ServiceAgreement.from_ddo(ServiceTypes.CLOUD_COMPUTE, compute_ddo)
    dt = publisher_ocean_instance.get_data_token(compute_ddo.data_token_address)
    mint_tokens_and_wait(dt, pub_acc.address, pub_acc)

    ######
    # Order compute service from the dataset asset
    # TODO: implement the ocean.compute.order method
    order_requirements = cons_ocn.compute.order(
        compute_ddo.did,
        consumer_account,
        None,
        None
    )

    ######
    # Transfer tokens to the provider as specified in the `order` requirements
    try:
        tx_id = dt.transfer(consumer_account.address, order_requirements['numTokens'], pub_acc)
        dt.verify_transfer_tx(tx_id, pub_acc.address, consumer_account.address)
    except (AssertionError, Exception) as e:
        print(e)
        raise

    ######
    job_id = cons_ocn.compute.start(did, consumer_account, algorithm_meta=algorithm_meta)
    assert job_id, f'expected a job id, got {job_id}'

    status = cons_ocn.compute.status(did, job_id, consumer_account)
    print(f'got job status: {status}')
    assert status and status['ok'], f'something not right about the compute job, got status: {status}'

    status = cons_ocn.compute.stop(did, job_id, consumer_account)
    print(f'got job status after requesting stop: {status}')
    assert status, f'something not right about the compute job, got status: {status}'

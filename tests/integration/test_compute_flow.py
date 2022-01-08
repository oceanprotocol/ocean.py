#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from typing import List, Optional

import pytest
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.trusted_algorithms import create_publisher_trusted_algorithms
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import (
    get_registered_algorithm_ddo,
    get_registered_algorithm_ddo_different_provider,
    get_registered_ddo_with_access_service,
    get_registered_ddo_with_compute_service,
    wait_for_update,
)
from web3.logs import DISCARD


@pytest.fixture
def dataset_with_compute_service(publisher_wallet, publisher_ocean_instance):
    # Dataset with compute service
    asset = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher_wallet
    )

    # verify the ddo is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)

    yield asset


@pytest.fixture
def algorithm(publisher_wallet, publisher_ocean_instance):
    # Setup algorithm meta to run raw algorithm
    asset = get_registered_algorithm_ddo(publisher_ocean_instance, publisher_wallet)
    # verify the ddo is available in Aquarius
    _ = publisher_ocean_instance.assets.resolve(asset.did)

    yield asset


@pytest.fixture
def dataset_with_compute_service_and_trusted_algorithm(
    publisher_wallet, publisher_ocean_instance, algorithm
):
    # Setup algorithm meta to run raw algorithm
    asset = get_registered_ddo_with_compute_service(
        publisher_ocean_instance, publisher_wallet, trusted_algorithms=[algorithm.did]
    )
    # verify the ddo is available in Aquarius
    _ = publisher_ocean_instance.assets.resolve(asset.did)

    yield asset


def process_order(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    asset: Asset,
    service_type: str,
):
    """Helper function to process a compute order."""
    # Mint 10 datatokens to the consumer
    service = asset.get_service(service_type)
    erc20_token = ERC20Token(ocean_instance.web3, service.data_token)
    _ = erc20_token.mint(consumer_wallet.address, to_wei(10), publisher_wallet)

    # Initialize the service to get provider fees
    _, initialize_url = DataServiceProvider.build_initialize_endpoint(
        ocean_instance.config.provider_url
    )
    initialize_response = DataServiceProvider.initialize(
        did=asset.did,
        service_id=service.id,
        consumer_address=consumer_wallet.address,
        service_endpoint=initialize_url,
        # TODO: add a real compute environment
        compute_environment="doesn't matter for now",
    ).json()

    # Order the service
    order_tx_id = erc20_token.start_order(
        consumer=consumer_wallet.address,
        service_id=int(service.id),
        provider_fees=initialize_response["providerFee"],
        from_wallet=consumer_wallet,
    )

    return order_tx_id, service


def run_compute_test(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    dataset: Asset,
    algorithm: Asset,
    additional_datasets: Optional[List[Asset]] = [],
    expect_failure=False,
    expect_failure_message=None,
    userdata=None,
    with_result=False,
):
    """Helper function to bootstrap compute job creation and status checking."""
    # Order asset compute service
    order_tx_id, compute_service = process_order(
        ocean_instance,
        publisher_wallet,
        consumer_wallet,
        dataset,
        ServiceTypes.CLOUD_COMPUTE,
    )
    compute_inputs = [
        ComputeInput(dataset.did, order_tx_id, compute_service.id, userdata=userdata)
    ]

    # Order algo download service
    algo_tx_id, algo_download_service = process_order(
        ocean_instance,
        publisher_wallet,
        consumer_wallet,
        algorithm,
        ServiceTypes.ASSET_ACCESS,
    )

    for asset in additional_datasets:
        service_type = ServiceTypes.ASSET_ACCESS
        if not asset.get_service(service_type):
            service_type = ServiceTypes.CLOUD_COMPUTE
        _order_tx_id, _order_quote, _service = process_order(
            ocean_instance, publisher_wallet, consumer_wallet, asset, service_type
        )
        compute_inputs.append(
            ComputeInput(asset.did, _order_tx_id, _service.index, userdata=userdata)
        )

    # Start compute job
    job_id = DataServiceProvider.start_compute_job(
        did=dataset.did,
        service_endpoint=DataServiceProvider.build_compute_endpoint(
            ocean_instance.config.provider_uri
        ),
        consumer=consumer_wallet.address,
        service_id=compute_service.id,
        order_tx_id=order_tx_id,
        algorithm_did=algorithm.did,
        algorithm_tx_id=algo_tx_id,
        algorithm_data_token=algo_download_service.data_token,
    )

    status = ocean_instance.compute.status(dataset.did, job_id, consumer_wallet)
    print(f"got job status: {status}")

    assert (
        status and status["ok"]
    ), f"something not right about the compute job, got status: {status}"

    status = ocean_instance.compute.stop(dataset.did, job_id, consumer_wallet)
    print(f"got job status after requesting stop: {status}")
    assert status, f"something not right about the compute job, got status: {status}"

    if with_result:
        result = ocean_instance.compute.result(dataset.did, job_id, consumer_wallet)
        print(f"got job status after requesting result: {result}")
        assert "did" in result, "something not right about the compute job, no did."

        succeeded = False
        for _ in range(0, 200):
            status = ocean_instance.compute.status(dataset.did, job_id, consumer_wallet)
            # wait until job is done, see:
            # https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description
            if status["status"] > 60:
                succeeded = True
                break
            time.sleep(5)

        assert succeeded, "compute job unsuccessful"
        result_file = ocean_instance.compute.result_file(
            dataset.did, job_id, 0, consumer_wallet
        )
        assert result_file is not None
        print(f"got job result file: {str(result_file)}")


def test_compute_raw_algo(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service,
    algorithm,
):
    """Tests that a compute job with a raw algorithm starts properly."""
    # Setup algorithm meta to run raw algorithm
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset=dataset_with_compute_service,
        algorithm=algorithm,
        with_result=True,
    )


@pytest.mark.skip(reason="TODO: reinstate integration tests")
def test_compute_multi_inputs(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service,
):
    """Tests that a compute job with additional Inputs (multiple assets) starts properly."""
    # Another dataset, this time with download service
    another_dataset = get_registered_ddo_with_access_service(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = publisher_ocean_instance.assets.resolve(another_dataset.did)

    # Setup algorithm meta to run raw algorithm
    algorithm = get_registered_algorithm_ddo_different_provider(
        publisher_ocean_instance, publisher_wallet
    )
    _ = publisher_ocean_instance.assets.resolve(algorithm.did)

    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset=dataset_with_compute_service,
        algorithm=algorithm,
        userdata={"test_key": "test_value"},
    )


@pytest.mark.skip(reason="TODO: reinstate integration tests")
def test_update_trusted_algorithms(
    web3,
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    consumer_ocean_instance,
    algorithm_ddo,
    asset_with_trusted,
):
    # TODO: outdated, left for inspuration in v4
    # ddo_address = get_contracts_addresses(config.address_file, "ganache")["v3"]
    # ddo_registry = MetadataContract(web3, ddo_address)
    ddo_registry = None

    trusted_algo_list = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], publisher_ocean_instance.config.metadata_cache_uri
    )
    asset_with_trusted.update_compute_privacy(
        trusted_algorithms=trusted_algo_list,
        trusted_algo_publishers=[],
        allow_all=False,
        allow_raw_algorithm=False,
    )

    tx_id = publisher_ocean_instance.assets.update(asset_with_trusted, publisher_wallet)

    tx_receipt = ddo_registry.get_tx_receipt(web3, tx_id)
    logs = ddo_registry.event_MetadataUpdated.processReceipt(tx_receipt, errors=DISCARD)
    assert logs[0].args.dataToken == asset_with_trusted.data_token_address

    wait_for_update(
        publisher_ocean_instance,
        asset_with_trusted.did,
        "privacy",
        {"publisherTrustedAlgorithms": [algorithm_ddo.did]},
    )

    compute_ddo_updated = publisher_ocean_instance.assets.resolve(
        asset_with_trusted.did
    )

    run_compute_test(
        consumer_ocean_instance,
        publisher_wallet,
        consumer_wallet,
        [compute_ddo_updated],
        algorithm=algorithm_ddo,
    )


@pytest.mark.skip(reason="TODO: reinstate integration tests")
def test_compute_trusted_algorithms(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    consumer_ocean_instance,
    algorithm_ddo,
    asset_with_trusted,
):
    algorithm_ddo_v2 = get_registered_algorithm_ddo(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = publisher_ocean_instance.assets.resolve(algorithm_ddo_v2.did)

    # For debugging.
    run_compute_test(
        consumer_ocean_instance,
        publisher_wallet,
        consumer_wallet,
        [asset_with_trusted],
        algorithm=algorithm_ddo,
    )

    # Expect to fail with another algorithm ddo that is not trusted.
    run_compute_test(
        consumer_ocean_instance,
        publisher_wallet,
        consumer_wallet,
        [asset_with_trusted],
        algorithm=algorithm_ddo_v2,
        expect_failure=True,
        expect_failure_message=f"this algorithm did {algorithm_ddo_v2.did} is not trusted.",
    )

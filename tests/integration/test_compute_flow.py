#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import pytest
from attr import dataclass

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.trusted_algorithms import create_publisher_trusted_algorithms
from ocean_lib.exceptions import DataProviderException
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import (
    get_raw_algorithm,
    get_registered_algorithm_with_access_service,
    get_registered_asset_with_access_service,
    get_registered_asset_with_compute_service,
)


@pytest.fixture
def dataset_with_compute_service(publisher_wallet, publisher_ocean_instance):
    """Returns a dataset with compute service.
    Fixture is registered on chain once and can be used multiple times.
    Reduces setup time."""
    # Dataset with compute service
    asset = get_registered_asset_with_compute_service(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the asset is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


@pytest.fixture
def dataset_with_compute_service_generator(publisher_wallet, publisher_ocean_instance):
    """Returns a new dataset each time fixture is used.
    Useful for tests that need to update the dataset"""
    # Dataset with compute service
    asset = get_registered_asset_with_compute_service(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the asset is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    yield asset


@pytest.fixture
def dataset_with_compute_service_allow_raw_algo(
    publisher_wallet, publisher_ocean_instance
):
    # Dataset with compute service
    asset = get_registered_asset_with_compute_service(
        publisher_ocean_instance, publisher_wallet, allow_raw_algorithms=True
    )
    # verify the asset is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


@pytest.fixture
def dataset_with_compute_service_and_trusted_algorithm(
    publisher_wallet, publisher_ocean_instance, algorithm
):
    # Setup algorithm meta to run raw algorithm
    asset = get_registered_asset_with_compute_service(
        publisher_ocean_instance, publisher_wallet, trusted_algorithms=[algorithm]
    )
    # verify the ddo is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


@pytest.fixture
def dataset_with_compute_service_and_trusted_publisher(
    publisher_wallet, publisher_ocean_instance
):
    # Setup algorithm meta to run raw algorithm
    asset = get_registered_asset_with_compute_service(
        publisher_ocean_instance,
        publisher_wallet,
        trusted_algorithm_publishers=[publisher_wallet.address],
    )
    # verify the ddo is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


def get_algorithm(publisher_wallet, publisher_ocean_instance):
    # Setup algorithm meta to run raw algorithm
    asset = get_registered_algorithm_with_access_service(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the asset is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


@pytest.fixture
def algorithm(publisher_wallet, publisher_ocean_instance):
    return get_algorithm(publisher_wallet, publisher_ocean_instance)


@pytest.fixture
def algorithm_with_different_publisher(consumer_wallet, publisher_ocean_instance):
    return get_algorithm(consumer_wallet, publisher_ocean_instance)


@pytest.fixture
def raw_algorithm():
    return get_raw_algorithm()


@pytest.fixture
def dataset_with_access_service(publisher_wallet, publisher_ocean_instance):
    # Dataset with access service
    asset = get_registered_asset_with_access_service(
        publisher_ocean_instance, publisher_wallet
    )
    # verify the asset is available in Aquarius
    publisher_ocean_instance.assets.resolve(asset.did)
    return asset


def process_order(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    asset: Asset,
    service_type: str,
) -> Tuple[str, Service]:
    """Helper function to process a compute order."""
    # Mint 10 datatokens to the consumer
    service = asset.get_service(service_type)
    erc20_token = ERC20Token(ocean_instance.web3, service.datatoken)

    # for the "algorithm with different publisher fixture, consumer is minter
    minter = (
        consumer_wallet
        if erc20_token.is_minter(consumer_wallet.address)
        else publisher_wallet
    )
    erc20_token.mint(consumer_wallet.address, to_wei(10), minter)

    environments = ocean_instance.compute.get_c2d_environments(service.service_endpoint)

    order_tx_id = ocean_instance.assets.pay_for_service(
        asset=asset,
        service=service,
        wallet=consumer_wallet,
        initialize_args={
            "compute_environment": environments[0]["id"],
            "valid_until": int((datetime.now() + timedelta(hours=1)).timestamp()),
        },
        consumer_address=environments[0]["consumerAddress"],
    )

    return order_tx_id, service


@dataclass
class AssetAndUserdata:
    asset: Asset
    userdata: Optional[dict]


def run_compute_test(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    dataset_and_userdata: AssetAndUserdata,
    algorithm_and_userdata: Optional[AssetAndUserdata] = None,
    algorithm_meta: Optional[AlgorithmMetadata] = None,
    algorithm_algocustomdata: Optional[dict] = None,
    additional_datasets_and_userdata: List[AssetAndUserdata] = [],
    with_result=False,
):
    """Helper function to bootstrap compute job creation and status checking."""
    assert (
        algorithm_and_userdata or algorithm_meta
    ), "either algorithm_and_userdata or algorithm_meta must be provided."

    # Order dataset with compute service
    dataset_tx_id, compute_service = process_order(
        ocean_instance,
        publisher_wallet,
        consumer_wallet,
        dataset_and_userdata.asset,
        ServiceTypes.CLOUD_COMPUTE,
    )
    dataset = ComputeInput(
        dataset_and_userdata.asset.did,
        dataset_tx_id,
        compute_service.id,
        dataset_and_userdata.userdata,
    )

    # Order additional datasets
    additional_datasets = []
    for asset_and_userdata in additional_datasets_and_userdata:
        service_type = ServiceTypes.ASSET_ACCESS
        if not asset_and_userdata.asset.get_service(service_type):
            service_type = ServiceTypes.CLOUD_COMPUTE
        _order_tx_id, _service = process_order(
            ocean_instance,
            publisher_wallet,
            consumer_wallet,
            asset_and_userdata.asset,
            service_type,
        )
        additional_datasets.append(
            ComputeInput(
                asset_and_userdata.asset.did,
                _order_tx_id,
                _service.id,
                asset_and_userdata.userdata,
            )
        )

    # Order algo download service (aka. access service)
    algorithm = None
    if algorithm_and_userdata:
        algo_tx_id, algo_download_service = process_order(
            ocean_instance,
            publisher_wallet,
            consumer_wallet,
            algorithm_and_userdata.asset,
            ServiceTypes.ASSET_ACCESS,
        )
        algorithm = ComputeInput(
            algorithm_and_userdata.asset.did,
            algo_tx_id,
            algo_download_service.id,
            algorithm_and_userdata.userdata,
        )

    service = dataset_and_userdata.asset.get_service(ServiceTypes.CLOUD_COMPUTE)
    environments = ocean_instance.compute.get_c2d_environments(service.service_endpoint)

    # Start compute job
    job_id = ocean_instance.compute.start(
        consumer_wallet,
        dataset,
        environments[0]["id"],
        algorithm,
        algorithm_meta,
        algorithm_algocustomdata,
        additional_datasets,
    )

    status = ocean_instance.compute.status(
        dataset_and_userdata.asset, job_id, consumer_wallet
    )
    print(f"got job status: {status}")

    assert (
        status and status["ok"]
    ), f"something not right about the compute job, got status: {status}"

    status = ocean_instance.compute.stop(
        dataset_and_userdata.asset, job_id, consumer_wallet
    )
    print(f"got job status after requesting stop: {status}")
    assert status, f"something not right about the compute job, got status: {status}"

    if with_result:
        succeeded = False
        for _ in range(0, 200):
            status = ocean_instance.compute.status(
                dataset_and_userdata.asset, job_id, consumer_wallet
            )
            # wait until job is done, see:
            # https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description
            if status["status"] > 60:
                succeeded = True
                break
            time.sleep(5)

        assert succeeded, "compute job unsuccessful"
        result_file = ocean_instance.compute.result(
            dataset_and_userdata.asset, job_id, 0, consumer_wallet
        )
        assert result_file is not None
        print(f"got job result file: {str(result_file)}")


def test_compute_raw_algo(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service_allow_raw_algo,
    raw_algorithm,
    dataset_with_compute_service,
):
    """Tests that a compute job with a raw algorithm starts properly."""
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(
            dataset_with_compute_service_allow_raw_algo, None
        ),
        algorithm_meta=raw_algorithm,
    )

    with pytest.raises(
        DataProviderException, match="cannot run raw algorithm on this did"
    ):
        run_compute_test(
            ocean_instance=publisher_ocean_instance,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(dataset_with_compute_service, None),
            algorithm_meta=raw_algorithm,
        )


def test_compute_registered_algo(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service,
    algorithm,
):
    """Tests that a compute job with a registered algorithm starts properly."""
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(dataset_with_compute_service, None),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
    )


def test_compute_multi_inputs(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service,
    algorithm,
    dataset_with_access_service,
):
    """Tests that a compute job with additional Inputs (multiple assets) starts properly."""
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(dataset_with_compute_service, None),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
        additional_datasets_and_userdata=[
            AssetAndUserdata(dataset_with_access_service, {"test_key": "test_value"})
        ],
    )


def test_compute_trusted_algorithm(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service_and_trusted_algorithm,
    algorithm,
    algorithm_with_different_publisher,
):
    # Expect to pass when trusted algorithm is used
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(
            dataset_with_compute_service_and_trusted_algorithm, None
        ),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
    )

    # Expect to fail when non-trusted algorithm is used
    with pytest.raises(
        DataProviderException,
        match=f"this algorithm did {algorithm_with_different_publisher.did} is not trusted",
    ):
        run_compute_test(
            ocean_instance=publisher_ocean_instance,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                dataset_with_compute_service_and_trusted_algorithm, None
            ),
            algorithm_and_userdata=AssetAndUserdata(
                algorithm_with_different_publisher, None
            ),
        )


def test_compute_update_trusted_algorithm(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service_generator,
    algorithm,
    algorithm_with_different_publisher,
):
    trusted_algo_list = create_publisher_trusted_algorithms([algorithm], "")
    dataset_with_compute_service_generator.update_compute_values(
        trusted_algorithms=trusted_algo_list,
        trusted_algo_publishers=[],
        allow_network_access=True,
        allow_raw_algorithm=False,
    )

    updated_dataset = publisher_ocean_instance.assets.update(
        dataset_with_compute_service_generator, publisher_wallet
    )

    # Expect to pass when trusted algorithm is used
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(updated_dataset, None),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
        with_result=True,
    )

    # Expect to fail when non-trusted algorithm is used
    with pytest.raises(
        DataProviderException,
        match=f"this algorithm did {algorithm_with_different_publisher.did} is not trusted",
    ):
        run_compute_test(
            ocean_instance=publisher_ocean_instance,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(updated_dataset, None),
            algorithm_and_userdata=AssetAndUserdata(
                algorithm_with_different_publisher, None
            ),
            with_result=True,
        )


def test_compute_trusted_publisher(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service_and_trusted_publisher,
    algorithm,
    algorithm_with_different_publisher,
):
    # Expect to pass when algorithm with trusted publisher is used
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(
            dataset_with_compute_service_and_trusted_publisher, None
        ),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
    )

    # Expect to fail when algorithm with non-trusted publisher is used
    with pytest.raises(
        DataProviderException, match="this algorithm is not from a trusted publisher"
    ):
        run_compute_test(
            ocean_instance=publisher_ocean_instance,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                dataset_with_compute_service_and_trusted_publisher, None
            ),
            algorithm_and_userdata=AssetAndUserdata(
                algorithm_with_different_publisher, None
            ),
        )

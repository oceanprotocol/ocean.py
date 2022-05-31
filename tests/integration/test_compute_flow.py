#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from datetime import datetime, timedelta
from typing import List, Optional

import pytest
from attr import dataclass

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.exceptions import DataProviderException
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
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


@dataclass
class AssetAndUserdata:
    asset: Asset
    userdata: Optional[dict]


def _mint_and_build_compute_input(
    dataset_and_userdata: AssetAndUserdata,
    service_type: str,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    ocean_instance: Ocean,
) -> ComputeInput:
    service = get_first_service_by_type(dataset_and_userdata.asset, service_type)
    datatoken = Datatoken(ocean_instance.web3, service.datatoken)
    minter = (
        consumer_wallet
        if datatoken.is_minter(consumer_wallet.address)
        else publisher_wallet
    )
    datatoken.mint(consumer_wallet.address, to_wei(10), minter)

    return ComputeInput(
        dataset_and_userdata.asset,
        service,
        userdata=dataset_and_userdata.userdata,
        consume_market_order_fee_token=datatoken.address,
        consume_market_order_fee_amount=0,
    )


def run_compute_test(
    ocean_instance: Ocean,
    publisher_wallet: Wallet,
    consumer_wallet: Wallet,
    dataset_and_userdata: AssetAndUserdata,
    algorithm_and_userdata: Optional[AssetAndUserdata] = None,
    algorithm_meta: Optional[AlgorithmMetadata] = None,
    algorithm_algocustomdata: Optional[dict] = None,
    additional_datasets_and_userdata: List[AssetAndUserdata] = [],
    scenarios: Optional[List[str]] = None,
):
    """Helper function to bootstrap compute job creation and status checking."""
    assert (
        algorithm_and_userdata or algorithm_meta
    ), "either algorithm_and_userdata or algorithm_meta must be provided."

    if not scenarios:
        scenarios = []

    datasets = [
        _mint_and_build_compute_input(
            dataset_and_userdata,
            ServiceTypes.CLOUD_COMPUTE,
            publisher_wallet,
            consumer_wallet,
            ocean_instance,
        )
    ]

    # build additional datasets
    for asset_and_userdata in additional_datasets_and_userdata:
        service_type = ServiceTypes.ASSET_ACCESS
        if not get_first_service_by_type(asset_and_userdata.asset, service_type):
            service_type = ServiceTypes.CLOUD_COMPUTE

        datasets.append(
            _mint_and_build_compute_input(
                asset_and_userdata,
                service_type,
                publisher_wallet,
                consumer_wallet,
                ocean_instance,
            )
        )

    # Order algo download service (aka. access service)
    algorithm = None
    if algorithm_and_userdata:
        algorithm = _mint_and_build_compute_input(
            algorithm_and_userdata,
            ServiceTypes.ASSET_ACCESS,
            publisher_wallet,
            consumer_wallet,
            ocean_instance,
        )

    service = get_first_service_by_type(
        dataset_and_userdata.asset, ServiceTypes.CLOUD_COMPUTE
    )

    environments = ocean_instance.compute.get_c2d_environments(service.service_endpoint)

    time_difference = (
        timedelta(hours=1) if "reuse_order" not in scenarios else timedelta(seconds=30)
    )

    if "just_fees" in scenarios:
        fees_response = ocean_instance.retrieve_provider_fees_for_compute(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=environments[0]["consumerAddress"],
            compute_environment=environments[0]["id"],
            valid_until=int((datetime.utcnow() + time_difference).timestamp()),
        )

        assert "algorithm" in fees_response
        assert len(fees_response["datasets"]) == 1

        return

    datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
        datasets,
        algorithm if algorithm else algorithm_meta,
        consumer_address=environments[0]["consumerAddress"],
        compute_environment=environments[0]["id"],
        valid_until=int((datetime.utcnow() + time_difference).timestamp()),
        consume_market_order_fee_address=consumer_wallet.address,
        wallet=consumer_wallet,
    )

    # Start compute job
    job_id = ocean_instance.compute.start(
        consumer_wallet,
        datasets[0],
        environments[0]["id"],
        algorithm,
        algorithm_meta,
        algorithm_algocustomdata,
        datasets[1:],
    )

    status = ocean_instance.compute.status(
        dataset_and_userdata.asset, service, job_id, consumer_wallet
    )
    print(f"got job status: {status}")

    assert (
        status and status["ok"]
    ), f"something not right about the compute job, got status: {status}"

    status = ocean_instance.compute.stop(
        dataset_and_userdata.asset, service, job_id, consumer_wallet
    )
    print(f"got job status after requesting stop: {status}")
    assert status, f"something not right about the compute job, got status: {status}"

    if "with_result" in scenarios:
        succeeded = False
        for _ in range(0, 200):
            status = ocean_instance.compute.status(
                dataset_and_userdata.asset, service, job_id, consumer_wallet
            )
            # wait until job is done, see:
            # https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description
            if status["status"] > 60:
                succeeded = True
                break
            time.sleep(5)

        print(f"got status: {status}")
        assert succeeded, "compute job unsuccessful"

        log_file = ocean_instance.compute.compute_job_result_logs(
            dataset_and_userdata.asset, service, job_id, consumer_wallet, "algorithmLog"
        )
        assert "Applying Gaussian processing." in str(log_file[0])
        print(f"got algo log file: {str(log_file)}")

        result = ocean_instance.compute.result(
            dataset_and_userdata.asset, service, job_id, 0, consumer_wallet
        )
        assert result

        prev_dt_tx_id = datasets[0].transfer_tx_id
        prev_algo_tx_id = algorithm.transfer_tx_id

        # retry initialize but all orders are already valid
        datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=environments[0]["consumerAddress"],
            compute_environment=environments[0]["id"],
            valid_until=int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            consume_market_order_fee_address=consumer_wallet.address,
            wallet=consumer_wallet,
        )

        # transferTxId was not updated
        assert datasets[0].transfer_tx_id == prev_dt_tx_id
        assert algorithm.transfer_tx_id == prev_algo_tx_id

    if "reuse_order" in scenarios:
        prev_dt_tx_id = datasets[0].transfer_tx_id
        prev_algo_tx_id = algorithm.transfer_tx_id
        # ensure order expires
        time.sleep(time_difference.seconds + 1)
        datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=environments[0]["consumerAddress"],
            compute_environment=environments[0]["id"],
            valid_until=int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            consume_market_order_fee_address=consumer_wallet.address,
            wallet=consumer_wallet,
        )

        assert datasets[0].transfer_tx_id != prev_dt_tx_id
        assert algorithm.transfer_tx_id != prev_algo_tx_id

        job_id = ocean_instance.compute.start(
            consumer_wallet,
            datasets[0],
            environments[0]["id"],
            algorithm,
            algorithm_meta,
            algorithm_algocustomdata,
            datasets[1:],
        )

        assert job_id, "can not reuse order"


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
def test_compute_reuse_order(
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
        scenarios=["reuse_order"],
    )


@pytest.mark.integration
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


@pytest.mark.integration
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


@pytest.mark.integration
def test_compute_update_trusted_algorithm(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service_generator,
    algorithm,
    algorithm_with_different_publisher,
):
    trusted_algo_list = [algorithm.generate_trusted_algorithms()]
    compute_service = get_first_service_by_type(
        dataset_with_compute_service_generator, "compute"
    )

    compute_service.update_compute_values(
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
        scenarios=["with_result"],
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
            scenarios=["with_result"],
        )


@pytest.mark.integration
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


@pytest.mark.integration
def test_compute_just_provider_fees(
    publisher_wallet,
    publisher_ocean_instance,
    consumer_wallet,
    dataset_with_compute_service,
    algorithm,
):
    """Tests that the correct compute provider fees are calculated."""
    run_compute_test(
        ocean_instance=publisher_ocean_instance,
        publisher_wallet=publisher_wallet,
        consumer_wallet=consumer_wallet,
        dataset_and_userdata=AssetAndUserdata(dataset_with_compute_service, None),
        algorithm_and_userdata=AssetAndUserdata(algorithm, None),
        scenarios=["just_fees"],
    )

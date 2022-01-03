#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

import pytest
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.trusted_algorithms import create_publisher_trusted_algorithms
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.data_token import DataToken
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import (
    get_algorithm_meta,
    get_registered_algorithm_ddo,
    get_registered_algorithm_ddo_different_provider,
    get_registered_ddo_with_access_service,
    get_registered_ddo_with_compute_service,
    wait_for_update,
)
from tests.resources.helper_functions import (
    get_consumer_ocean_instance,
    get_consumer_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
)
from web3.logs import DISCARD


class Setup:
    def __init__(self):
        """Initialise shared variables."""
        self.publisher_wallet = get_publisher_wallet()
        self.consumer_wallet = get_consumer_wallet()
        self.publisher_ocean_instance = get_publisher_ocean_instance()
        self.consumer_ocean_instance = get_consumer_ocean_instance()


@pytest.fixture
def setup():
    return Setup()


@pytest.fixture
def simple_compute_ddo():
    setup = Setup()
    # Dataset with compute service
    simple_compute_ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )

    # verify the ddo is available in Aquarius
    setup.publisher_ocean_instance.assets.resolve(simple_compute_ddo.did)

    yield simple_compute_ddo


@pytest.fixture
def algorithm_ddo():
    setup = Setup()
    # Setup algorithm meta to run raw algorithm
    algorithm_ddo = get_registered_algorithm_ddo(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo.did)

    yield algorithm_ddo


@pytest.fixture
def asset_with_trusted(algorithm_ddo):
    setup = Setup()
    # Setup algorithm meta to run raw algorithm
    ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance,
        setup.publisher_wallet,
        trusted_algorithms=[algorithm_ddo.did],
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(ddo.did)

    yield ddo


def process_order(ocean_instance, publisher_wallet, consumer_wallet, ddo, service_type):
    """Helper function to process a compute order."""
    # Give the consumer some datatokens so they can order the service
    try:
        dt = DataToken(ocean_instance.web3, ddo.data_token_address)
        tx_id = dt.transfer(consumer_wallet.address, to_wei(10), publisher_wallet)
        dt.verify_transfer_tx(tx_id, publisher_wallet.address, consumer_wallet.address)
    except (AssertionError, Exception) as e:
        print(e)
        raise

    # Order compute service from the dataset asset
    order_requirements = ocean_instance.assets.order(
        ddo.did, consumer_wallet.address, service_type=service_type
    )

    # Start the order on-chain using the `order` requirements from previous step
    service = ddo.get_service(service_type)
    consumer = service.get_c2d_address()
    if service_type == ServiceTypes.ASSET_ACCESS and order_requirements.computeAddress:
        consumer = order_requirements.computeAddress

    _order_tx_id = ocean_instance.assets.pay_for_service(
        ocean_instance.web3,
        order_requirements.amount,
        order_requirements.data_token_address,
        ddo.did,
        service.index,
        ZERO_ADDRESS,
        consumer_wallet,
        consumer,
    )
    return _order_tx_id, order_requirements, service


def run_compute_test(
    ocean_instance,
    publisher_wallet,
    consumer_wallet,
    input_ddos,
    algo_ddo=None,
    algo_meta=None,
    expect_failure=False,
    expect_failure_message=None,
    userdata=None,
    with_result=False,
):
    """Helper function to bootstrap compute job creation and status checking."""
    compute_ddo = input_ddos[0]
    did = compute_ddo.did
    order_tx_id, _, service = process_order(
        ocean_instance,
        publisher_wallet,
        consumer_wallet,
        compute_ddo,
        ServiceTypes.CLOUD_COMPUTE,
    )
    compute_inputs = [ComputeInput(did, order_tx_id, service.index, userdata=userdata)]
    for ddo in input_ddos[1:]:
        service_type = ServiceTypes.ASSET_ACCESS
        if not ddo.get_service(service_type):
            service_type = ServiceTypes.CLOUD_COMPUTE

        _order_tx_id, _order_quote, _service = process_order(
            ocean_instance, publisher_wallet, consumer_wallet, ddo, service_type
        )
        compute_inputs.append(
            ComputeInput(ddo.did, _order_tx_id, _service.index, userdata=userdata)
        )

    job_id = None
    if algo_ddo:
        # order the algo download service
        algo_tx_id, _, _ = process_order(
            ocean_instance,
            publisher_wallet,
            consumer_wallet,
            algo_ddo,
            ServiceTypes.ASSET_ACCESS,
        )
        try:
            job_id = ocean_instance.compute.start(
                compute_inputs,
                consumer_wallet,
                algorithm_did=algo_ddo.did,
                algorithm_tx_id=algo_tx_id,
                algorithm_data_token=algo_ddo.data_token_address,
                algouserdata={"algo_test": "algouserdata_sample"},
            )
        except Exception:
            if not expect_failure:
                raise
            return
    else:
        assert algo_meta, "algo_meta is required when not using algo_ddo."
        try:
            job_id = ocean_instance.compute.start(
                compute_inputs, consumer_wallet, algorithm_meta=algo_meta
            )
        except Exception:
            if not expect_failure:
                raise
            return

    if not expect_failure:
        assert expect_failure_message is None
        assert job_id, f"expected a job id, got {job_id}"

    status = ocean_instance.compute.status(did, job_id, consumer_wallet)
    print(f"got job status: {status}")

    assert (
        status and status["ok"]
    ), f"something not right about the compute job, got status: {status}"

    status = ocean_instance.compute.stop(did, job_id, consumer_wallet)
    print(f"got job status after requesting stop: {status}")
    assert status, f"something not right about the compute job, got status: {status}"

    if with_result:
        result = ocean_instance.compute.result(did, job_id, consumer_wallet)
        print(f"got job status after requesting result: {result}")
        assert "did" in result, "something not right about the compute job, no did."

        succeeded = False
        for _ in range(0, 200):
            status = ocean_instance.compute.status(did, job_id, consumer_wallet)
            # wait until job is done, see:
            # https://github.com/oceanprotocol/operator-service/blob/main/API.md#status-description
            if status["status"] > 60:
                succeeded = True
                break
            time.sleep(5)

        assert succeeded, "compute job unsuccessful"
        result_file = ocean_instance.compute.result_file(
            did, job_id, 0, consumer_wallet
        )
        assert result_file is not None
        print(f"got job result file: {str(result_file)}")


def test_compute_raw_algo(simple_compute_ddo):
    """Tests that a compute job with a raw algorithm starts properly."""
    setup = Setup()

    # Setup algorithm meta to run raw algorithm
    algorithm_meta = get_algorithm_meta()
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [simple_compute_ddo],
        algo_meta=algorithm_meta,
        with_result=True,
    )


def test_compute_multi_inputs(simple_compute_ddo):
    """Tests that a compute job with additional Inputs (multiple assets) starts properly."""
    setup = Setup()

    # Another dataset, this time with download service
    access_ddo = get_registered_ddo_with_access_service(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(access_ddo.did)

    # Setup algorithm meta to run raw algorithm
    algorithm_ddo = get_registered_algorithm_ddo_different_provider(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo.did)

    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [simple_compute_ddo, access_ddo],
        algo_ddo=algorithm_ddo,
        userdata={"test_key": "test_value"},
    )


def test_update_trusted_algorithms(config, web3, algorithm_ddo, asset_with_trusted):
    setup = Setup()

    # TODO: outdated, left for inspuration in v4
    # ddo_address = get_contracts_addresses(config.address_file, "ganache")["v3"]
    # ddo_registry = MetadataContract(web3, ddo_address)
    ddo_registry = None

    trusted_algo_list = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], setup.publisher_ocean_instance.config.metadata_cache_uri
    )
    asset_with_trusted.update_compute_privacy(
        trusted_algorithms=trusted_algo_list,
        trusted_algo_publishers=[],
        allow_all=False,
        allow_raw_algorithm=False,
    )

    tx_id = setup.publisher_ocean_instance.assets.update(
        asset_with_trusted, setup.publisher_wallet
    )

    tx_receipt = ddo_registry.get_tx_receipt(web3, tx_id)
    logs = ddo_registry.event_MetadataUpdated.processReceipt(tx_receipt, errors=DISCARD)
    assert logs[0].args.dataToken == asset_with_trusted.data_token_address

    wait_for_update(
        setup.publisher_ocean_instance,
        asset_with_trusted.did,
        "privacy",
        {"publisherTrustedAlgorithms": [algorithm_ddo.did]},
    )

    compute_ddo_updated = setup.publisher_ocean_instance.assets.resolve(
        asset_with_trusted.did
    )

    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [compute_ddo_updated],
        algo_ddo=algorithm_ddo,
    )


def test_compute_trusted_algorithms(algorithm_ddo, asset_with_trusted):
    setup = Setup()

    algorithm_ddo_v2 = get_registered_algorithm_ddo(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo_v2.did)

    # For debugging.
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [asset_with_trusted],
        algo_ddo=algorithm_ddo,
    )

    # Expect to fail with another algorithm ddo that is not trusted.
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [asset_with_trusted],
        algo_ddo=algorithm_ddo_v2,
        expect_failure=True,
        expect_failure_message=f"this algorithm did {algorithm_ddo_v2.did} is not trusted.",
    )

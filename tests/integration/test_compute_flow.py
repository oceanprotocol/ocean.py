#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.assets.utils import create_publisher_trusted_algorithms
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.metadata import MetadataContract
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_utils.agreements.service_types import ServiceTypes
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


class Setup:
    def __init__(self):
        """Initialise shared variables."""
        self.publisher_wallet = get_publisher_wallet()
        self.consumer_wallet = get_consumer_wallet()
        self.publisher_ocean_instance = get_publisher_ocean_instance()
        self.consumer_ocean_instance = get_consumer_ocean_instance()


def process_order(ocean_instance, publisher_wallet, consumer_wallet, ddo, service_type):
    """Helper function to process a compute order."""
    # Give the consumer some datatokens so they can order the service
    try:
        dt = DataToken(ddo.data_token_address)
        tx_id = dt.transfer_tokens(consumer_wallet.address, 10.0, publisher_wallet)
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
    consumer = consumer_wallet.address
    if service_type == ServiceTypes.ASSET_ACCESS and order_requirements.computeAddress:
        consumer = order_requirements.computeAddress

    _order_tx_id = ocean_instance.assets.pay_for_service(
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
    restart_and_result=False,
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
    compute_inputs = [ComputeInput(did, order_tx_id, service.index)]
    for ddo in input_ddos[1:]:
        service_type = ServiceTypes.ASSET_ACCESS
        if not ddo.get_service(service_type):
            service_type = ServiceTypes.CLOUD_COMPUTE

        _order_tx_id, _order_quote, _service = process_order(
            ocean_instance, publisher_wallet, consumer_wallet, ddo, service_type
        )
        compute_inputs.append(ComputeInput(ddo.did, _order_tx_id, _service.index))

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

    if restart_and_result:
        # TODO: test restart function after pending rework
        # OR delete this TODO if restart is removed from the interface

        result = ocean_instance.compute.result(did, job_id, consumer_wallet)
        print(f"got job status after requesting result: {result}")
        assert "did" in result, "something not right about the compute job, no did."


def test_compute_raw_algo():
    """Tests that a compute job with a raw algorithm starts properly."""
    setup = Setup()

    # Dataset with compute service
    compute_ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(compute_ddo.did)

    # Setup algorithm meta to run raw algorithm
    algorithm_meta = get_algorithm_meta()
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [compute_ddo],
        algo_meta=algorithm_meta,
        restart_and_result=True,
    )


def test_compute_multi_inputs():
    """Tests that a compute job with additional Inputs (multiple assets) starts properly."""
    setup = Setup()

    # Dataset with compute service
    compute_ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(compute_ddo.did)

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
        [compute_ddo, access_ddo],
        algo_ddo=algorithm_ddo,
    )


def test_update_trusted_algorithms():
    setup = Setup()

    config = ConfigProvider.get_config()
    ddo_address = get_contracts_addresses("ganache", config)[
        MetadataContract.CONTRACT_NAME
    ]
    ddo_registry = MetadataContract(ddo_address)

    # Setup algorithm meta to run raw algorithm
    algorithm_ddo = get_registered_algorithm_ddo(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo.did)

    # Dataset with compute service
    compute_ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance,
        setup.publisher_wallet,
        trusted_algorithms=[algorithm_ddo.did],
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(compute_ddo.did)
    trusted_algo_list = create_publisher_trusted_algorithms(
        [algorithm_ddo.did], setup.publisher_ocean_instance.config.aquarius_url
    )
    compute_ddo.update_compute_privacy(
        trusted_algorithms=trusted_algo_list, allow_all=False, allow_raw_algorithm=False
    )

    tx_id = setup.publisher_ocean_instance.assets.update(
        compute_ddo, setup.publisher_wallet
    )

    tx_receipt = ddo_registry.get_tx_receipt(tx_id)
    logs = ddo_registry.event_MetadataUpdated.processReceipt(tx_receipt)
    assert logs[0].args.dataToken == compute_ddo.data_token_address

    wait_for_update(
        setup.publisher_ocean_instance,
        compute_ddo.did,
        "privacy",
        {"publisherTrustedAlgorithms": [algorithm_ddo.did]},
    )

    compute_ddo_updated = setup.publisher_ocean_instance.assets.resolve(compute_ddo.did)

    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [compute_ddo_updated],
        algo_ddo=algorithm_ddo,
    )


def test_compute_trusted_algorithms():
    setup = Setup()

    # Setup algorithm meta to run raw algorithm
    algorithm_ddo = get_registered_algorithm_ddo(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo.did)

    algorithm_ddo_v2 = get_registered_algorithm_ddo(
        setup.publisher_ocean_instance, setup.publisher_wallet
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(algorithm_ddo_v2.did)

    # Dataset with compute service
    compute_ddo = get_registered_ddo_with_compute_service(
        setup.publisher_ocean_instance,
        setup.publisher_wallet,
        trusted_algorithms=[algorithm_ddo.did],
    )
    # verify the ddo is available in Aquarius
    _ = setup.publisher_ocean_instance.assets.resolve(compute_ddo.did)

    # For debugging.
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [compute_ddo],
        algo_ddo=algorithm_ddo,
    )

    # Expect to fail with another algorithm ddo that is not trusted.
    run_compute_test(
        setup.consumer_ocean_instance,
        setup.publisher_wallet,
        setup.consumer_wallet,
        [compute_ddo],
        algo_ddo=algorithm_ddo_v2,
        expect_failure=True,
        expect_failure_message=f"this algorithm did {algorithm_ddo_v2.did} is not trusted.",
    )

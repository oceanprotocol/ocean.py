#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from datetime import datetime, timedelta
from typing import List, Optional

import pytest
import requests
from attr import dataclass

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import get_config_dict
from ocean_lib.exceptions import DataProviderException
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.util import to_wei
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from tests.resources.ddo_helpers import (
    get_first_service_by_type,
    get_registered_asset_with_compute_service,
)
from tests.resources.helper_functions import (
    get_consumer_wallet,
    get_publisher_ocean_instance,
    get_publisher_wallet,
)


class TestComputeFlow(object):
    @classmethod
    def setup_class(self):
        publisher_wallet = get_publisher_wallet()
        consumer_wallet = get_consumer_wallet()
        publisher_ocean = get_publisher_ocean_instance()
        _, _, ddo = get_registered_asset_with_compute_service(
            publisher_ocean, publisher_wallet
        )

        self.dataset_with_compute_service = ddo

        _, _, ddo = get_registered_asset_with_compute_service(
            publisher_ocean, publisher_wallet, allow_raw_algorithms=True
        )

        self.dataset_with_compute_service_allow_raw_algo = ddo

        _, _, ddo = get_registered_asset_with_compute_service(
            publisher_ocean, publisher_wallet
        )

        self.dataset_for_update = ddo

        _, _, ddo = get_registered_asset_with_compute_service(
            publisher_ocean,
            publisher_wallet,
            trusted_algorithm_publishers=[publisher_wallet.address],
        )

        self.dataset_with_compute_service_and_trusted_publisher = ddo
        self.algorithm = get_algorithm(publisher_wallet, publisher_ocean)
        self.algorithm_with_different_publisher = get_algorithm(
            consumer_wallet, publisher_ocean
        )

        self.published_ddos = {}

    def wait_for_ddo(self, ddo):
        if ddo.did not in self.published_ddos:
            config = get_config_dict()
            data_provider = DataServiceProvider
            ocean_assets = OceanAssets(config, data_provider)
            ddo = ocean_assets._aquarius.wait_for_ddo(ddo.did)
            self.published_ddos[ddo.did] = ddo

        return self.published_ddos[ddo.did]

    @pytest.mark.integration
    def test_compute_raw_algo(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
        raw_algorithm,
    ):
        """Tests that a compute job with a raw algorithm starts properly."""
        self.wait_for_ddo(self.dataset_with_compute_service_allow_raw_algo)

        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service_allow_raw_algo, None
            ),
            algorithm_meta=raw_algorithm,
        )

        self.wait_for_ddo(self.dataset_with_compute_service)
        with pytest.raises(DataProviderException, match="no_raw_algo_allowed"):
            run_compute_test(
                ocean_instance=publisher_ocean,
                publisher_wallet=publisher_wallet,
                consumer_wallet=consumer_wallet,
                dataset_and_userdata=AssetAndUserdata(
                    self.dataset_with_compute_service, None
                ),
                algorithm_meta=raw_algorithm,
            )

    @pytest.mark.integration
    def test_compute_registered_algo(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
    ):
        """Tests that a compute job with a registered algorithm starts properly."""
        self.wait_for_ddo(self.dataset_with_compute_service)
        self.wait_for_ddo(self.algorithm)

        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service, None
            ),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
        )

    @pytest.mark.integration
    def test_compute_reuse_order(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
    ):
        """Tests that a compute job with a registered algorithm starts properly."""
        self.wait_for_ddo(self.dataset_with_compute_service)
        self.wait_for_ddo(self.algorithm)

        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service, None
            ),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
            scenarios=["reuse_order"],
        )

    @pytest.mark.integration
    def test_compute_multi_inputs(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
        basic_asset,
    ):
        """Tests that a compute job with additional Inputs (multiple assets) starts properly."""
        _, _, dataset_with_access_service = basic_asset
        self.wait_for_ddo(self.dataset_with_compute_service)
        self.wait_for_ddo(self.algorithm)

        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service, None
            ),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
            additional_datasets_and_userdata=[
                AssetAndUserdata(
                    dataset_with_access_service, {"test_key": "test_value"}
                )
            ],
        )

    @pytest.mark.integration
    def test_compute_trusted_algorithm(self):
        # functionality covered in test_compute_update_trusted_algorithm
        assert True

    @pytest.mark.integration
    def test_compute_update_trusted_algorithm(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
    ):
        self.wait_for_ddo(self.dataset_for_update)
        self.wait_for_ddo(self.algorithm)

        trusted_algo_list = [self.algorithm.generate_trusted_algorithms()]
        compute_service = get_first_service_by_type(self.dataset_for_update, "compute")

        compute_service.update_compute_values(
            trusted_algorithms=trusted_algo_list,
            trusted_algo_publishers=[],
            allow_network_access=True,
            allow_raw_algorithm=False,
        )

        updated_dataset = publisher_ocean.assets.update(
            self.dataset_for_update, {"from": publisher_wallet}
        )

        # Expect to pass when trusted algorithm is used
        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(updated_dataset, None),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
            scenarios=["with_result"],
        )

        self.wait_for_ddo(self.algorithm_with_different_publisher)
        # Expect to fail when non-trusted algorithm is used
        with pytest.raises(
            DataProviderException,
            match="not_trusted_algo",
        ):
            run_compute_test(
                ocean_instance=publisher_ocean,
                publisher_wallet=publisher_wallet,
                consumer_wallet=consumer_wallet,
                dataset_and_userdata=AssetAndUserdata(updated_dataset, None),
                algorithm_and_userdata=AssetAndUserdata(
                    self.algorithm_with_different_publisher, None
                ),
                scenarios=["with_result"],
            )

    @pytest.mark.integration
    def test_compute_trusted_publisher(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
    ):
        self.wait_for_ddo(self.dataset_with_compute_service_and_trusted_publisher)
        self.wait_for_ddo(self.algorithm)

        # Expect to pass when algorithm with trusted publisher is used
        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service_and_trusted_publisher, None
            ),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
        )

        self.wait_for_ddo(self.algorithm_with_different_publisher)

        # Expect to fail when algorithm with non-trusted publisher is used
        with pytest.raises(DataProviderException, match="not_trusted_algo_publisher"):
            run_compute_test(
                ocean_instance=publisher_ocean,
                publisher_wallet=publisher_wallet,
                consumer_wallet=consumer_wallet,
                dataset_and_userdata=AssetAndUserdata(
                    self.dataset_with_compute_service_and_trusted_publisher, None
                ),
                algorithm_and_userdata=AssetAndUserdata(
                    self.algorithm_with_different_publisher, None
                ),
            )

    @pytest.mark.integration
    def test_compute_just_provider_fees(
        self,
        publisher_wallet,
        publisher_ocean,
        consumer_wallet,
    ):
        self.wait_for_ddo(self.dataset_with_compute_service)
        self.wait_for_ddo(self.algorithm)

        """Tests that the correct compute provider fees are calculated."""
        run_compute_test(
            ocean_instance=publisher_ocean,
            publisher_wallet=publisher_wallet,
            consumer_wallet=consumer_wallet,
            dataset_and_userdata=AssetAndUserdata(
                self.dataset_with_compute_service, None
            ),
            algorithm_and_userdata=AssetAndUserdata(self.algorithm, None),
            scenarios=["just_fees"],
        )


def get_algorithm(wallet, ocean_instance):
    # Setup algorithm meta to run raw algorithm
    _, _, ddo = ocean_instance.assets.create_algo_asset(
        name="Sample asset",
        url="https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py",
        tx_dict={"from": wallet},
        image="oceanprotocol/algo_dockers",
        tag="python-branin",
        checksum="sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
        wait_for_aqua=False,
    )
    # verify the asset is available in Aquarius
    ocean_instance.assets.resolve(ddo.did)
    return ddo


@pytest.fixture
def raw_algorithm():
    req = requests.get(
        "https://raw.githubusercontent.com/oceanprotocol/test-algorithm/master/javascript/algo.js"
    )
    return AlgorithmMetadata(
        {
            "rawcode": req.text,
            "language": "Node.js",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": "oceanprotocol/algo_dockers",
                "tag": "python-branin",
                "checksum": "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
            },
        }
    )


@dataclass
class AssetAndUserdata:
    ddo: DDO
    userdata: Optional[dict]


def _mint_and_build_compute_input(
    dataset_and_userdata: AssetAndUserdata,
    service_type: str,
    publisher_wallet,
    consumer_wallet,
    ocean_instance: Ocean,
) -> ComputeInput:
    service = get_first_service_by_type(dataset_and_userdata.ddo, service_type)
    datatoken = DatatokenBase.get_typed(ocean_instance.config_dict, service.datatoken)
    minter = (
        consumer_wallet
        if datatoken.isMinter(consumer_wallet.address)
        else publisher_wallet
    )
    datatoken.mint(consumer_wallet.address, to_wei(10), {"from": minter})

    return ComputeInput(
        dataset_and_userdata.ddo,
        service,
        userdata=dataset_and_userdata.userdata,
        consume_market_order_fee_token=datatoken.address,
        consume_market_order_fee_amount=0,
    )


def run_compute_test(
    ocean_instance: Ocean,
    publisher_wallet,
    consumer_wallet,
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
        if not get_first_service_by_type(asset_and_userdata.ddo, service_type):
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
        dataset_and_userdata.ddo, ServiceTypes.CLOUD_COMPUTE
    )

    try:
        free_c2d_env = ocean_instance.compute.get_free_c2d_environment(
            service.service_endpoint, 8996
        )
    except StopIteration:
        assert False, "No free c2d environment found."

    time_difference = (
        timedelta(hours=1) if "reuse_order" not in scenarios else timedelta(seconds=30)
    )
    valid_until = int((datetime.utcnow() + time_difference).timestamp())

    if "just_fees" in scenarios:
        fees_response = ocean_instance.retrieve_provider_fees_for_compute(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=free_c2d_env["consumerAddress"],
            compute_environment=free_c2d_env["id"],
            valid_until=valid_until,
        )

        assert "algorithm" in fees_response
        assert len(fees_response["datasets"]) == 1

        return

    datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
        datasets,
        algorithm if algorithm else algorithm_meta,
        consumer_address=free_c2d_env["consumerAddress"],
        compute_environment=free_c2d_env["id"],
        valid_until=valid_until,
        consume_market_order_fee_address=consumer_wallet.address,
        tx_dict={"from": consumer_wallet},
    )

    # Start compute job
    job_id = ocean_instance.compute.start(
        consumer_wallet,
        datasets[0],
        free_c2d_env["id"],
        algorithm,
        algorithm_meta,
        algorithm_algocustomdata,
        datasets[1:],
    )

    status = ocean_instance.compute.status(
        dataset_and_userdata.ddo, service, job_id, consumer_wallet
    )
    print(f"got job status: {status}")

    assert (
        status and status["ok"]
    ), f"something not right about the compute job, got status: {status}"

    status = ocean_instance.compute.stop(
        dataset_and_userdata.ddo, service, job_id, consumer_wallet
    )
    print(f"got job status after requesting stop: {status}")
    assert status, f"something not right about the compute job, got status: {status}"

    if "with_result" in scenarios:
        succeeded = False
        for _ in range(0, 200):
            status = ocean_instance.compute.status(
                dataset_and_userdata.ddo, service, job_id, consumer_wallet
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
            dataset_and_userdata.ddo, service, job_id, consumer_wallet, "algorithmLog"
        )
        print(f"got algo log file: {str(log_file)}")

        _ = ocean_instance.compute.result(
            dataset_and_userdata.ddo, service, job_id, 0, consumer_wallet
        )

        prev_dt_tx_id = datasets[0].transfer_tx_id
        prev_algo_tx_id = algorithm.transfer_tx_id

        # retry initialize but all orders are already valid
        datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=free_c2d_env["consumerAddress"],
            compute_environment=free_c2d_env["id"],
            valid_until=valid_until,
            consume_market_order_fee_address=consumer_wallet.address,
            tx_dict={"from": consumer_wallet},
        )

        # transferTxId was not updated
        assert datasets[0].transfer_tx_id == prev_dt_tx_id
        assert algorithm.transfer_tx_id == prev_algo_tx_id

    if "reuse_order" in scenarios:
        prev_dt_tx_id = datasets[0].transfer_tx_id
        prev_algo_tx_id = algorithm.transfer_tx_id
        # ensure order expires
        time.sleep(time_difference.seconds + 1)

        valid_until = int((datetime.utcnow() + time_difference).timestamp())
        datasets, algorithm = ocean_instance.assets.pay_for_compute_service(
            datasets,
            algorithm if algorithm else algorithm_meta,
            consumer_address=free_c2d_env["consumerAddress"],
            compute_environment=free_c2d_env["id"],
            valid_until=valid_until,
            consume_market_order_fee_address=consumer_wallet.address,
            tx_dict={"from": consumer_wallet},
        )

        assert datasets[0].transfer_tx_id != prev_dt_tx_id
        assert algorithm.transfer_tx_id != prev_algo_tx_id

        job_id = ocean_instance.compute.start(
            consumer_wallet,
            datasets[0],
            free_c2d_env["id"],
            algorithm,
            algorithm_meta,
            algorithm_algocustomdata,
            datasets[1:],
        )

        assert job_id, "can not reuse order"

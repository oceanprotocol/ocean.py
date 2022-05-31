#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import UrlFile
from tests.resources.ddo_helpers import get_first_service_by_type
from tests.resources.helper_functions import generate_wallet


def c2d_flow_readme(
    ocean,
    dataset_name,
    dataset_url,
    algorithm_name,
    algorithm_url,
    algorithm_docker_tag,
):
    consumer_wallet = publisher_wallet = generate_wallet()
    # Publish the data NFT token
    data_nft = ocean.create_data_nft("NFTToken1", "NFT1", publisher_wallet)
    assert data_nft.address
    assert data_nft.token_name()
    assert data_nft.symbol()

    # Publish the datatoken
    DATA_datatoken = data_nft.create_datatoken(
        "Datatoken 1",
        "DT1",
        from_wallet=publisher_wallet,
    )
    assert DATA_datatoken.address

    # Specify metadata and services, using the Branin test dataset
    DATA_date_created = "2021-12-28T10:55:11Z"

    DATA_metadata = {
        "created": DATA_date_created,
        "updated": DATA_date_created,
        "description": dataset_name,
        "name": dataset_name,
        "type": "dataset",
        "author": "Trent",
        "license": "CC0: PublicDomain",
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    DATA_url_file = UrlFile(url=dataset_url)

    # Encrypt file(s) using provider
    DATA_encrypted_files = ocean.assets.encrypt_files([DATA_url_file])

    # Set the compute values for compute service
    DATA_compute_values = {
        "allowRawAlgorithm": False,
        "allowNetworkAccess": True,
        "publisherTrustedAlgorithms": [],
        "publisherTrustedAlgorithmPublishers": [],
    }

    # Create the Service
    DATA_compute_service = Service(
        service_id="2",
        service_type="compute",
        service_endpoint=ocean.config.provider_url,
        datatoken=DATA_datatoken.address,
        files=DATA_encrypted_files,
        timeout=3600,
        compute_values=DATA_compute_values,
    )

    # Publish asset with compute service on-chain.
    DATA_asset = ocean.assets.create(
        metadata=DATA_metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=DATA_encrypted_files,
        services=[DATA_compute_service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[DATA_datatoken],
    )

    assert DATA_asset.did, "create dataset with compute service unsuccessful"

    # Publish the algorithm NFT token
    ALGO_nft_token = ocean.create_data_nft("NFTToken1", "NFT1", publisher_wallet)
    assert ALGO_nft_token.address

    # Publish the datatoken
    ALGO_datatoken = ALGO_nft_token.create_datatoken(
        "Datatoken 1",
        "DT1",
        from_wallet=publisher_wallet,
    )
    assert ALGO_datatoken.address

    # Specify metadata and services, using the Branin test dataset
    ALGO_date_created = "2021-12-28T10:55:11Z"

    ALGO_metadata = {
        "created": ALGO_date_created,
        "updated": ALGO_date_created,
        "description": algorithm_name,
        "name": algorithm_name,
        "type": "algorithm",
        "author": "Trent",
        "license": "CC0: PublicDomain",
        "algorithm": {
            "language": "python",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": "oceanprotocol/algo_dockers",
                "tag": algorithm_docker_tag,
                "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
            },
        },
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    ALGO_url_file = UrlFile(url=algorithm_url)

    # Encrypt file(s) using provider
    ALGO_encrypted_files = ocean.assets.encrypt_files([ALGO_url_file])

    # Publish asset with compute service on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    ALGO_asset = ocean.assets.create(
        metadata=ALGO_metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=ALGO_encrypted_files,
        data_nft_address=ALGO_nft_token.address,
        deployed_datatokens=[ALGO_datatoken],
    )

    assert ALGO_asset.did, "create algorithm unsuccessful"

    compute_service = DATA_asset.services[0]
    compute_service.add_publisher_trusted_algorithm(ALGO_asset)
    DATA_asset = ocean.assets.update(DATA_asset, publisher_wallet)

    DATA_datatoken.mint(consumer_wallet.address, ocean.to_wei(5), publisher_wallet)
    ALGO_datatoken.mint(consumer_wallet.address, ocean.to_wei(5), publisher_wallet)

    # Convenience variables
    DATA_did = DATA_asset.did
    ALGO_did = ALGO_asset.did

    # Operate on updated and indexed assets
    DATA_asset = ocean.assets.resolve(DATA_did)
    ALGO_asset = ocean.assets.resolve(ALGO_did)

    compute_service = get_first_service_by_type(DATA_asset, "compute")
    algo_service = get_first_service_by_type(ALGO_asset, "access")

    environments = ocean.compute.get_c2d_environments(compute_service.service_endpoint)

    DATA_compute_input = ComputeInput(DATA_did, compute_service.id)
    ALGO_compute_input = ComputeInput(ALGO_did, algo_service.id)

    # Pay for dataset
    datasets, algorithm = ocean.assets.pay_for_compute_service(
        datasets=[DATA_compute_input],
        algorithm_data=ALGO_compute_input,
        consume_market_order_fee_address=consumer_wallet.address,
        wallet=consumer_wallet,
        compute_environment=environments[0]["id"],
        valid_until=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        consumer_address=environments[0]["consumerAddress"],
    )
    assert datasets, "pay for dataset unsuccessful"
    assert algorithm, "pay for algorithm unsuccessful"

    # Start compute job
    job_id = ocean.compute.start(
        consumer_wallet=consumer_wallet,
        dataset=datasets[0],
        compute_environment=environments[0]["id"],
        algorithm=algorithm,
    )
    assert job_id, "start compute unsuccessful"

    # Wait until job is done
    succeeded = False
    for _ in range(0, 200):
        status = ocean.compute.status(
            DATA_asset, compute_service, job_id, consumer_wallet
        )
        if status.get("dateFinished") and Decimal(status["dateFinished"]) > 0:
            print(f"Status = '{status}'")
            succeeded = True
            break
        time.sleep(5)
    assert succeeded, "compute job unsuccessful"

    # Retrieve algorithm output and log files
    output = None
    for i in range(len(status["results"])):
        result_type = status["results"][i]["type"]
        print(f"Fetch result index {i}, type: {result_type}")
        result = ocean.compute.result(
            DATA_asset, compute_service, job_id, i, consumer_wallet
        )
        assert result, "result retrieval unsuccessful"
        print(f"result index: {i}, type: {result_type}, contents: {result}")

        # Extract algorithm output
        if result_type == "output":
            output = result
    assert output, "algorithm output not found"
    unpickle_result(output)


def unpickle_result(pickled):
    """Unpickle the gaussian model result"""
    model = pickle.loads(pickled)
    assert len(model) > 0, "unpickle result unsuccessful"


def concurrent_c2d(concurrent_flows: int, repetitions: int):
    config = ExampleConfig.get_config()
    ocean = Ocean(config)
    mint_fake_OCEAN(config)
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * repetitions):
            executor.submit(
                c2d_flow_readme,
                ocean,
                "brainin",
                "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/branin.arff",
                "gpr",
                "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py",
                "python-brain",
            )


@pytest.mark.slow
@pytest.mark.parametrize(
    ["concurrent_flows", "repetitions"], [(1, 300), (3, 100), (20, 5)]
)
def test_concurrent_c2d(concurrent_flows, repetitions):
    concurrent_c2d(concurrent_flows, repetitions)

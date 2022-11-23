#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import io
import os
import pickle
import time
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from brownie.network import accounts
from PIL import Image
from web3.main import Web3

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import UrlFile


@pytest.mark.slow
@pytest.mark.parametrize(
    "dataset_name,dataset_url,algorithm_name,algorithm_url,algorithm_docker_tag,docker_digest",
    [
        (
            "lena",
            "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/peppers_and_grayscale/peppers.tiff",
            "grayscale",
            "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/peppers_and_grayscale/grayscale.py",
            "python-branin",
            "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
        ),
        (
            "iris",
            "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/iris_and_logisitc_regression/dataset_61_iris.csv",
            "logistic-regression",
            "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/iris_and_logisitc_regression/logistic_regression.py",
            "python-panda",
            "sha256:7fc268f502935d11ff50c54e3776dda76477648d5d83c2e3c4fdab744390ecf2",
        ),
    ],
)
def test_c2d_flow_more_examples_readme(
    dataset_name,
    dataset_url,
    algorithm_name,
    algorithm_url,
    algorithm_docker_tag,
    docker_digest,
):
    """This test mirrors the c2d-flow-more-examples.md README.
    As such, it does not use the typical pytest fixtures.
    """
    c2d_flow_readme(
        dataset_name,
        dataset_url,
        algorithm_name,
        algorithm_url,
        algorithm_docker_tag,
        docker_digest,
    )


def c2d_flow_readme(
    dataset_name,
    dataset_url,
    algorithm_name,
    algorithm_url,
    algorithm_docker_tag,
    docker_digest,
):
    """This is a helper method that mirrors the c2d-flow.md README."""

    # 2. Alice publishes data asset with compute service
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = accounts.add(alice_private_key)
    assert alice_wallet.address

    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert accounts.at(alice_wallet.address).balance() > 0, "need ETH"

    # Publish the data NFT token
    data_nft = ocean.create_data_nft("NFT1", "NFT1", alice_wallet)
    assert data_nft.address
    assert data_nft.name()
    assert data_nft.symbol()

    # Publish the datatoken
    DATA_datatoken = data_nft.create_datatoken(
        "Datatoken 1",
        "DT1",
        from_wallet=alice_wallet,
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
    DATA_files = [DATA_url_file]

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
        service_endpoint=ocean.config_dict["PROVIDER_URL"],
        datatoken=DATA_datatoken.address,
        files=DATA_files,
        timeout=3600,
        compute_values=DATA_compute_values,
    )

    # Publish asset with compute service on-chain.
    DATA_ddo = ocean.assets.create(
        metadata=DATA_metadata,
        publisher_wallet=alice_wallet,
        files=DATA_files,
        services=[DATA_compute_service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[DATA_datatoken],
    )

    assert DATA_ddo.did, "create dataset with compute service unsuccessful"

    # 3. Alice publishes algorithm

    # Publish the algorithm NFT token
    ALGO_nft_token = ocean.create_data_nft("NFT1", "NFT1", alice_wallet)
    assert ALGO_nft_token.address

    # Publish the datatoken
    ALGO_datatoken = ALGO_nft_token.create_datatoken(
        "Datatoken 1",
        "DT1",
        from_wallet=alice_wallet,
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
                "checksum": docker_digest,
            },
        },
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    ALGO_url_file = UrlFile(url=algorithm_url)
    ALGO_files = [ALGO_url_file]

    # Publish asset with compute service on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    ALGO_ddo = ocean.assets.create(
        metadata=ALGO_metadata,
        publisher_wallet=alice_wallet,
        files=ALGO_files,
        data_nft_address=ALGO_nft_token.address,
        deployed_datatokens=[ALGO_datatoken],
    )

    assert ALGO_ddo.did, "create algorithm unsuccessful"

    # 4. Alice allows the algorithm for C2D for that data asset
    compute_service = DATA_ddo.services[0]
    compute_service.add_publisher_trusted_algorithm(ALGO_ddo)
    DATA_ddo = ocean.assets.update(DATA_ddo, alice_wallet)

    # 5. Bob acquires datatokens for data and algorithm
    bob_wallet = accounts.add("TEST_PRIVATE_KEY2")
    assert bob_wallet.address

    # Alice mints DATA datatokens and ALGO datatokens to Bob.
    # Alternatively, Bob might have bought these in a market.
    DATA_datatoken.mint(
        bob_wallet.address, Web3.toWei(5, "ether"), {"from": alice_wallet}
    )
    ALGO_datatoken.mint(
        bob_wallet.address, Web3.toWei(5, "ether"), {"from": alice_wallet}
    )

    # 6. Bob starts a compute job

    # Convenience variables
    DATA_did = DATA_ddo.did
    ALGO_did = ALGO_ddo.did

    # Operate on updated and indexed assets
    DATA_ddo = ocean.assets.resolve(DATA_did)
    ALGO_ddo = ocean.assets.resolve(ALGO_did)

    compute_service = DATA_ddo.services[0]
    algo_service = ALGO_ddo.services[0]

    free_c2d_env = ocean.compute.get_free_c2d_environment(
        compute_service.service_endpoint
    )

    DATA_compute_input = ComputeInput(DATA_ddo, compute_service)
    ALGO_compute_input = ComputeInput(ALGO_ddo, algo_service)

    # Pay for dataset and algo
    datasets, algorithm = ocean.assets.pay_for_compute_service(
        datasets=[DATA_compute_input],
        algorithm_data=ALGO_compute_input,
        consume_market_order_fee_address=bob_wallet.address,
        wallet=bob_wallet,
        compute_environment=free_c2d_env["id"],
        valid_until=int((datetime.utcnow() + timedelta(days=1)).timestamp()),
        consumer_address=free_c2d_env["consumerAddress"],
    )
    assert datasets, "pay for dataset unsuccessful"
    assert algorithm, "pay for algorithm unsuccessful"

    # Start compute job
    job_id = ocean.compute.start(
        consumer_wallet=bob_wallet,
        dataset=datasets[0],
        compute_environment=free_c2d_env["id"],
        algorithm=algorithm,
    )
    assert job_id, "start compute unsuccessful"

    # Wait until job is done
    succeeded = False
    for _ in range(0, 200):
        status = ocean.compute.status(DATA_ddo, compute_service, job_id, bob_wallet)
        if status.get("dateFinished") and Decimal(status["dateFinished"]) > 0:
            print(f"Status = '{status}'")
            succeeded = True
            break
        time.sleep(5)
    assert succeeded, "compute job unsuccessful"

    # Retrieve algorithm output and log files
    output = ocean.compute.compute_job_result_logs(
        DATA_ddo, compute_service, job_id, bob_wallet
    )[0]
    assert output, "algorithm output not found"

    if dataset_name == "branin" or dataset_name == "iris":
        unpickle_result(output)
    else:
        load_image(output)


def unpickle_result(pickled):
    """Unpickle the gaussian model result"""
    model = pickle.loads(pickled)
    assert len(model) > 0, "unpickle result unsuccessful"


def load_image(image_bytes):
    """Load the image result"""
    image = Image.open(io.BytesIO(image_bytes))
    assert image, "load image unsuccessful"

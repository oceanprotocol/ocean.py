#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import pickle
import time
from datetime import datetime, timedelta

import pytest

from ocean_lib.assets.trusted_algorithms import add_publisher_trusted_algorithm
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.structures.abi_tuples import ConsumeFees, CreateErc20Data
from ocean_lib.structures.file_objects import UrlFile
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


@pytest.mark.parametrize(
    "dataset_name,dataset_url,algorithm_name,algorithm_url",
    [
        (
            "Branin",
            "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff",
            "gpr,",
            "https://raw.githubusercontent.com/trentmc/branin/main/gpr.py",
        )
    ],
)
def test_c2d_flow_readme(dataset_name, dataset_url, algorithm_name, algorithm_url):
    """This test mirrors the c2d-flow.md README.
    As such, it does not use the typical pytest fixtures.
    """

    # 2. Alice publishes data asset with compute service
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address

    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

    # Publish the data NFT token
    DATA_nft_token = ocean.create_erc721_nft("NFTToken1", "NFT1", alice_wallet)
    assert DATA_nft_token.address

    # Publish the datatoken
    DATA_erc20_data = CreateErc20Data(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
            ocean.OCEAN_address,
        ],
        uints=[ocean.to_wei(100000), 0],
        bytess=[b""],
    )
    DATA_datatoken = DATA_nft_token.create_datatoken(DATA_erc20_data, alice_wallet)
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
        publisher_wallet=alice_wallet,
        encrypted_files=DATA_encrypted_files,
        services=[DATA_compute_service],
        erc721_address=DATA_nft_token.address,
        deployed_erc20_tokens=[DATA_datatoken],
    )

    assert DATA_asset.did, "create dataset with compute service unsuccessful"

    # 3. Alice publishes algorithm

    # Publish the algorithm NFT token
    ALGO_nft_token = ocean.create_erc721_nft("NFTToken1", "NFT1", alice_wallet)
    assert ALGO_nft_token.address

    # Publish the datatoken
    ALGO_erc20_data = CreateErc20Data(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
            ocean.OCEAN_address,
        ],
        uints=[ocean.to_wei(100000), 0],
        bytess=[b""],
    )
    ALGO_datatoken = ALGO_nft_token.create_datatoken(ALGO_erc20_data, alice_wallet)

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
                "tag": "python-branin",
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
        publisher_wallet=alice_wallet,
        encrypted_files=ALGO_encrypted_files,
        erc721_address=ALGO_nft_token.address,
        deployed_erc20_tokens=[ALGO_datatoken],
    )

    assert ALGO_asset.did, "create algorithm unsuccessful"

    # 4. Alice allows the algorithm for C2D for that data asset
    add_publisher_trusted_algorithm(
        DATA_asset, ALGO_asset.did, config.metadata_cache_uri
    )
    DATA_asset = ocean.assets.update(DATA_asset, alice_wallet)

    # 5. Bob acquires datatokens for data and algorithm
    bob_wallet = Wallet(
        ocean.web3,
        os.getenv("TEST_PRIVATE_KEY2"),
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert bob_wallet.address

    # Alice mints DATA datatokens and ALGO datatokens to Bob.
    # Alternatively, Bob might have bought these in a market.
    DATA_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
    ALGO_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)

    # 6. Bob starts a compute job

    # Convenience variables
    DATA_did = DATA_asset.did
    ALGO_did = ALGO_asset.did

    # Operate on updated and indexed assets
    DATA_asset = ocean.assets.resolve(DATA_did)
    ALGO_asset = ocean.assets.resolve(ALGO_did)

    compute_service = DATA_asset.get_service("compute")
    algo_service = ALGO_asset.get_service("access")

    environments = ocean.compute.get_c2d_environments(compute_service.service_endpoint)

    # Consume fees
    consume_fees = ConsumeFees(
        consumer_market_fee_address=bob_wallet.address,
        consumer_market_fee_token=DATA_datatoken.address,
        consumer_market_fee_amount=0,
    )

    # Pay for dataset
    DATA_order_tx_id = ocean.assets.pay_for_service(
        asset=DATA_asset,
        service=compute_service,
        consume_fees=consume_fees,
        wallet=bob_wallet,
        initialize_args={
            "compute_environment": environments[0]["id"],
            "valid_until": int((datetime.now() + timedelta(days=1)).timestamp()),
        },
        consumer_address=environments[0]["consumerAddress"],
    )
    assert DATA_order_tx_id, "pay for dataset unsuccessful"

    # Consume fees
    consume_fees = ConsumeFees(
        consumer_market_fee_address=bob_wallet.address,
        consumer_market_fee_token=ALGO_datatoken.address,
        consumer_market_fee_amount=0,
    )

    # Pay for algorithm
    ALGO_order_tx_id = ocean.assets.pay_for_service(
        asset=ALGO_asset,
        service=algo_service,
        consume_fees=consume_fees,
        wallet=bob_wallet,
        initialize_args={
            "valid_until": int((datetime.now() + timedelta(days=1)).timestamp())
        },
        consumer_address=environments[0]["consumerAddress"],
    )
    assert ALGO_order_tx_id, "pay for algorithm unsuccessful"

    # Start compute job
    DATA_compute_input = ComputeInput(DATA_did, DATA_order_tx_id, compute_service.id)
    ALGO_compute_input = ComputeInput(ALGO_did, ALGO_order_tx_id, algo_service.id)
    job_id = ocean.compute.start(
        consumer_wallet=bob_wallet,
        dataset=DATA_compute_input,
        compute_environment=environments[0]["id"],
        algorithm=ALGO_compute_input,
    )
    assert job_id, "start compute unsuccessful"

    # Wait until job is done
    succeeded = False
    for _ in range(0, 200):
        status = ocean.compute.status(DATA_asset, job_id, bob_wallet)
        if status.get("dateFinished") and int(status["dateFinished"]) > 0:
            print(f"Status = '{status}'")
            succeeded = True
            break
        time.sleep(5)
    assert succeeded, "compute job unsuccessful"

    # Retrieve algorithm output and log files
    output = None
    for i in range(len(status["results"])):
        result = None
        result_type = status["results"][i]["type"]
        print(f"Fetch result index {i}, type: {result_type}")
        result = ocean.compute.result(DATA_asset, job_id, i, bob_wallet)
        assert result, "result retrieval unsuccessful"

        # Extract algorithm output
        if result_type == "output":
            output = result
    assert output, "algorithm output not found"

    if dataset_name == "Branin":
        unpickle_gaussian_model_result(output)


def unpickle_gaussian_model_result(output):
    """Unpickle the gaussian model result"""
    model = pickle.loads(output)
    assert len(model) > 0, "unpickle result unsuccessful"

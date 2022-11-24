import datetime
from ocean_lib.web3_internal.utils import connect_to_network
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.ocean import Ocean
from brownie.network import accounts
from ocean_lib.services.service import Service

def upload_and_publish_C2D(setup, dataset, algorithm):

    print(f'\n\n\r\r----------------------------\n\rProcess started...\n\rPlease keep in mind that gas prices can have temporary spikes that might cause this process to fail\n\rIf the process fails because of gas you will see a message. Please try again.\n\r----------------------------\n\n\r\r')

    connect_to_network(setup['network'])

    config = ExampleConfig.get_config(setup['network'])
    ocean = Ocean(config)

    accounts.clear()

    alice_private_key = setup['PRIVATE_KEY']
    alice_wallet = accounts.add(alice_private_key)
    assert accounts.at(alice_wallet.address).balance() > 0, "Alice needs MATIC"


    # Publish data NFT & datatoken for dataset
    DATASET_data_nft = ocean.create_data_nft(dataset['NFT_name'], dataset['NFT_symbol'], alice_wallet)


    DATASET_datatoken = DATASET_data_nft.create_datatoken(dataset['NFT_name'], dataset['NFT_symbol'], from_wallet=alice_wallet)


    now = datetime.datetime.utcnow().isoformat()

    DATASET_metadata = {
    "created": now,
    "updated": now,
    "name": dataset['dataset_name'],
    "description": dataset['dataset_description'],
    "type": dataset['dataset_type'],
    "author": dataset['dataset_author'],
    "license": dataset['dataset_license'],
    }

    # make an enum with the object types so import depends on object type
    try:
        from ocean_lib.structures.file_objects import UrlFile
        DATASET_url_file = UrlFile(dataset['dataset_url'])
    except Exception as e:
        raise Exception(e)

    DATASET_files = [DATASET_url_file]

    DATASET_compute_values = {
    "allowRawAlgorithm": False,
    "allowNetworkAccess": True,
    "publisherTrustedAlgorithms": [],
    "publisherTrustedAlgorithmPublishers": [],
    }

    DATASET_compute_service = Service(
    service_id="2",
    service_type="compute",
    service_endpoint=ocean.config_dict["PROVIDER_URL"],
    datatoken=DATASET_datatoken.address,
    files=DATASET_files,
    timeout=3600,
    compute_values=DATASET_compute_values,
    )

    DATASET_asset = ocean.assets.create(
    metadata=DATASET_metadata,
    publisher_wallet=alice_wallet,
    files=DATASET_files,
    services=[DATASET_compute_service],
    data_nft_address=DATASET_data_nft.address,
    deployed_datatokens=[DATASET_datatoken],
    )



    # Publish data NFT & datatoken for algorithm
    ALGO_data_nft = ocean.create_data_nft(algorithm['ALGO_name'], algorithm['ALGO_symbol'], alice_wallet)


    ALGO_datatoken = ALGO_data_nft.create_datatoken(algorithm['ALGO_name'], algorithm['ALGO_symbol'], from_wallet=alice_wallet)


    ALGO_metadata = {
    "created": now,
    "updated": now,
    "description": algorithm['description'],
    "name": algorithm['name'],
    "type": algorithm['type'],
    "author": algorithm['author'],
    "license": algorithm['license'],
    "algorithm": algorithm['algorithm'],
    }

    # make an enum with the object types so import depends on object type
    try:
        from ocean_lib.structures.file_objects import UrlFile
        ALGO_url_file = UrlFile(algorithm['url'])
    except Exception as e:
        raise Exception(e)

    ALGO_files = [ALGO_url_file]

    ALGO_asset = ocean.assets.create(
    metadata=ALGO_metadata,
    publisher_wallet=alice_wallet,
    files=ALGO_files,
    data_nft_address=ALGO_data_nft.address,
    deployed_datatokens=[ALGO_datatoken],
)


    #ALLOW ALGORITHM FOR C2D ---------------------------
    compute_service = DATASET_asset.services[0]
    compute_service.add_publisher_trusted_algorithm(ALGO_asset)
    DATASET_asset = ocean.assets.update(DATASET_asset, alice_wallet)


    print(f'\n\n\r\r----------------------------\n\rThe process has ended successfully!\n\r\n\rYou have successfully published your dataset and your algorithm\n\rIt is now available for consumption\n\rPeople will now have to acquire your datatokens to get them.\n\r\n\rPlease save this data carefully. You will need it to manage your assets:\n\r\n\rDataset NFT Address: {DATASET_data_nft.address}\n\rDataset Token Address: {DATASET_datatoken.address}\n\rDataset Did: {DATASET_asset.did}\n\r\n\rAlgorithm NFT Address: {ALGO_data_nft.address}\n\rAlgorithm Token Address: {ALGO_datatoken.address}\n\rAlgorithm Did: {ALGO_asset.did}    ----------------------------\n\n\r\r')

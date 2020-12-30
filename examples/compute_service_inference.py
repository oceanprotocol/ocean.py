import json

from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.utils.utilities import get_timestamp

from ocean_lib.config import Config
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.bpool import BPool
from ocean_lib.models.data_token import DataToken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
import os


def get_config_dict():
    return {
        'eth-network': {
            'network': 'rinkeby',
        },
        'resources': {
            'aquarius.url': 'https://aquarius.rinkeby.v3.dev-ocean.com',
            'provider.url': 'https://provider.rinkeby.v3.dev-ocean.com'
        }
    }


def build_compute_descriptor(ocean, publisher):
    # build compute service metadata
    cluster_attributes = ocean.compute.build_cluster_attributes(cluster_type='Kubernetes', url='https://localhost:8050')
    supported_containers = [ocean.compute.build_container_attributes(image='huggingface/transformers-pytorch-gpu', tag='latest', entrypoint='python $ALGO')]
    servers = [ocean.compute.build_server_attributes(server_id='1', server_type='xlsize', cpu=8, gpu=1, memory='16gb', disk='200gb', max_run_time=3600)]
    provider_attributes = ocean.compute.build_service_provider_attributes(provider_type='AWS', description='GPU-V100 compute',
                                                                          cluster=cluster_attributes,
                                                                          containers=supported_containers,
                                                                          servers=servers)
    compute_attributes = ocean.compute.create_compute_service_attributes(timeout=3600, creator=publisher,
                                                                         date_published=get_timestamp(),
                                                                         provider_attributes=provider_attributes)
    return ocean.compute.create_compute_service_descriptor(compute_attributes)


def run_compute(ocean, did, consumer_wallet, algorithm_file, pool_address, order_id=None):
    #ocean = Ocean(config=Config(options_dict=get_config_dict()))

    # Get asset DDO/metadata and service
    asset = ocean.assets.resolve(did)
    service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)

    # check the price in ocean tokens
    num_ocean = ocean.pool.calcInGivenOut(pool_address, ocean.OCEAN_address, asset.data_token_address, 1.0)

    # buy datatoken to be able to run the compute service
    dt = DataToken(asset.asset_id)
    dt_balance = dt.token_balance(consumer_wallet.address)
    if dt_balance < 1.0:
        pool = BPool(pool_address)
        txid = ocean.pool.buy_data_tokens(pool_address, 1.0, num_ocean+0.1, consumer_wallet)
        receipt = pool.get_tx_receipt(txid)
        if not receipt or receipt.status != 1:
            print(f'buying data token failed: txId={txid}, txReceipt={receipt}')
            return None, None

    tx_id = order_id
    if not tx_id:
        tx_id = ocean.assets.pay_for_service(1.0, asset.data_token_address, did, service.index,
                                             fee_receiver=asset.publisher, from_wallet=consumer_wallet)

    # load python algorithm to run in the compute job
    with open(algorithm_file) as f:
        algorithm_text = f.read()

    # whether to publish the algorithm results as an Ocean assets
    output_dict = {
        'publishOutput': True,
        'publishAlgorithmLog': True,
    }
    # start the compute job (submit the compute service request)
    algorithm_meta = AlgorithmMetadata(
        {
            'language': 'python',
            'rawcode': algorithim_text,
            'container': {
                'tag': 'latest',
                'image': 'huggingface/transformers_gpu',
                'entrypoint': 'python $ALGO'
            }
        }
    )
    job_id = ocean.compute.start(did, consumer_wallet, tx_id, algorithm_meta=algorithm_meta, output=output_dict)

    # check the status of the compute job
    status = ocean.compute.status(did, job_id, consumer_wallet)
    print(f'status of compute job {job_id}: {status}')

    # get the result of the compute run
    result = ocean.compute.result(did, job_id, consumer_wallet)
    print(f'got result of compute job {job_id}: {result}')
    return job_id, status, result


def publish_asset(metadata, publisher_wallet):
    ocean = Ocean(config=Config(options_dict=get_config_dict()))

    # create compute service
    compute_descriptor = build_compute_descriptor(ocean, publisher_wallet.address)

    # create asset DDO and datatoken
    try:
        asset = ocean.assets.create(metadata, publisher_wallet, [compute_descriptor], dt_name='GPT-2 Pretrained', dt_symbol='GPT-2A')
        print(f'Dataset asset created successfully: did={asset.did}, datatoken={asset.data_token_address}')
        #Test1 Dataset asset created successfully: did=did:op:2cbDb0Aaa1F546829E31267d1a7F74d926Bb5B1B, datatoken=0x2cbDb0Aaa1F546829E31267d1a7F74d926Bb5B1B
        #Test2 Dataset asset created successfully: did=did:op:76D54fF1dE0753c99B788Bf3dAdf51b71bc944C1, datatoken=0x76D54fF1dE0753c99B788Bf3dAdf51b71bc944C1
        #GPT-2 Pretrained: Dataset asset created successfully: did=did:op:1015D1c5a047FF84B5157b982E8993F8b1e2FDA6, datatoken=0x1015D1c5a047FF84B5157b982E8993F8b1e2FDA6

    except Exception as e:
        print(f'Publishing asset failed: {e}')
        return None, None

    dt = DataToken(asset.data_token_address)
    txid = dt.mint_tokens(publisher_wallet.address, 100, publisher_wallet)
    receipt = dt.get_tx_receipt(txid)
    assert receipt and receipt.status == 1, f'datatoken mint failed: tx={txid}, txReceipt={receipt}'


    # Create datatoken liquidity pool for the new asset
    pool = ocean.pool.create(asset.data_token_address, 10, 5, publisher_wallet, 5) #50 datatokens - 5 ocean in pool
    print(f'datatoken liquidity pool was created at address {pool.address}')
    #Test1 datatoken liquidity pool was created at address 0xeaD638506951B4a4c3575bbC0c7D1491c17B7A08
    #Test2 datatoken liquidity pool was created at address 0x8229E15DaB16d9AaaDF0E1998C389020B9C973e2
    #GPT-2 datatoken liquidity pool was created at address 0xfd2E8e39EC0770b8e0427a395Fa7fd85EF03252C
    # Now the asset can be discovered and consumed
    dt_cost = ocean.pool.calcInGivenOut(pool.address, ocean.OCEAN_address, asset.data_token_address, 1.0)
    print(f'Asset {asset.did} can now be purchased from pool @{pool.address} '
          f'at the price of {dt_cost} OCEAN tokens.')
    return asset, pool


def main(did, pool_address, order_tx_id=None):
    ocean = Ocean(config=Config(options_dict=get_config_dict()))
    publisher = Wallet(ocean.web3, private_key='0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58')  # 0xe2DD09d719Da89e5a3D0F2549c7E24566e947260
    #consumer = Wallet(ocean.web3, private_key='0x9bf5d7e4978ed5206f760e6daded34d657572bd49fa5b3fe885679329fb16b16')  # 0x068Ed00cF0441e4829D9784fCBe7b9e26D4BD8d0
    publisher_wallet = Wallet(ocean.web3, private_key=os.getenv('Publisher_Key')) #addr: 0xc966Ba2a41888B6B4c5273323075B98E27B9F364
    consumer = Wallet(ocean.web3, private_key=os.getenv('Consumer_Key')) #addr: 0xEF5dc33A53DD2ED3F670B53F07cEc5ADD4D80504

    if not (did and pool_address):
        metadata_file = './examples/data/metadata.json'
        with open(metadata_file) as f:
            metadata = json.load(f)

        asset, pool = publish_asset(metadata, publisher)
        
    else:
        asset = ocean.assets.resolve(did)
        pool = BPool(pool_address)

    if not asset:
        print(f'publish asset failed, cannot continue with running compute.')
        return

    print(f'Requesting compute using asset {asset.did} and pool {pool.address}')
algo_file = './examples/data/Algo_inference.py'
#A prompt can be provided to Algo_inference as sys.argv[1]

#order_tx_id=
order_tx_id=''
job_id, status = run_compute(ocean, asset.did, consumer, algo_file, pool.address, order_tx_id)
    print(f'Compute started on asset {asset.did}: job_id={job_id}, status={status}')


if __name__ == '__main__':
    did = ''
    pool_address = ''
    order_tx_id = ''
    main(did, pool_address, order_tx_id)

#[eth-network]
#network = https://rinkeby.infura.io/v3/6ba6f1f72b954dc894e9d117fa37e013
#created new datatoken with address 0x2f7Bf183212a5Ac181614113636d7f9757b63d5a

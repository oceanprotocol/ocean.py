import lzma
import uuid

from eth_utils import add_0x_prefix
from ocean_utils.ddo.ddo import DDO
from ocean_utils.did import DID
from ocean_utils.utils.utilities import checksum

from ocean_lib.assets.asset import Asset
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.ddo import DDOContract
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.web3_provider import Web3Provider
from tests.resources.helper_functions import get_resource_path, get_publisher_wallet


def get_ddo_sample():
    sample_ddo_path = get_resource_path('ddo', 'ddo_sa_sample.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset = DDO(json_filename=sample_ddo_path)
    asset.metadata['main']['files'][0]['checksum'] = str(uuid.uuid4())

    checksum_dict = dict()
    for service in asset.services:
        checksum_dict[str(service.index)] = checksum(service.main)

    asset.add_proof(checksum_dict, get_publisher_wallet())
    asset._did = DID.did(asset.proof['checksum'])
    return asset


def test_ddo_on_chain():
    config = ConfigProvider.get_config()
    ddo_address = get_contracts_addresses('ganache', config)[DDOContract.CONTRACT_NAME]
    ddo_registry = DDOContract(ddo_address)
    wallet = get_publisher_wallet()
    web3 = Web3Provider.get_web3()

    # test create ddo
    asset = get_ddo_sample()
    old_name = asset.metadata['main']['name']
    txid = ddo_registry.create(
        asset.asset_id,
        b'',
        lzma.compress(web3.toBytes(text=asset.as_text())),
        wallet
    )
    assert ddo_registry.verify_tx(txid), f'create ddo failed: txid={txid}'
    logs = ddo_registry.events.DDOCreated().processReceipt(ddo_registry.get_tx_receipt(txid))
    assert logs, f'no logs found for create ddo tx {txid}'
    log = logs[0]
    assert add_0x_prefix(log.args.did.hex()) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), f'ddo text does not match original.'

    _asset = Asset(json_text=ddo_text)
    assert _asset.did == asset.did, f'did does not match.'
    name = _asset.metadata['main']['name']
    assert name == old_name, f'name does not match: {name} != {old_name}'

    # test_update ddo
    asset.metadata['main']['name'] = 'updated name for test'
    txid = ddo_registry.update(
        asset.asset_id,
        b'',
        lzma.compress(web3.toBytes(text=asset.as_text())),
        wallet
    )
    assert ddo_registry.verify_tx(txid), f'update ddo failed: txid={txid}'
    logs = ddo_registry.events.DDOUpdated().processReceipt(ddo_registry.get_tx_receipt(txid))
    if not logs:
        event = getattr(ddo_registry.events, 'DDOUpdated')
        # TODO: use the filter on tokenAddress when it is set as indexed in the contract event.
        filter_params = {}
        event_filter = EventFilter(
            'DDOUpdated',
            event,
            filter_params,
            from_block=0,
            to_block='latest'
        )
        logs = event_filter.get_all_entries(max_tries=10)

    assert logs, f'no logs found for update ddo tx {txid}'
    log = logs[0]
    assert add_0x_prefix(log.args.did.hex()) == asset.asset_id
    # read back the asset ddo from the event log
    ddo_text = web3.toText(lzma.decompress(log.args.data))
    assert ddo_text == asset.as_text(), f'ddo text does not match original.'
    _asset = Asset(json_text=ddo_text)
    assert _asset.metadata['main']['name'] == 'updated name for test', f'name does not seem to be updated.'

    # test ddoOwner

    # test transferOwnership

from web3 import WebsocketProvider

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.bfactory import BFactory
from ocean_lib.web3_internal.contract_handler import ContractHandler

from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider
from ocean_lib.web3_internal.web3helper import Web3Helper

WEB3_INFURA_PROJECT_ID = '357f2fe737db4304bd2f7285c5602d0d'

GANACHE_URL = 'http://127.0.0.1:8545'

SUPPORTED_NETWORK_NAMES = {'rinkeby', 'kovan', 'ganache', 'mainnet', 'ropsten'}


def get_infura_url(infura_id, network):
    return f"wss://{network}.infura.io/ws/v3/{infura_id}"


def get_web3_connection_provider(network_url):
    """
    Return the suitable web3 provider based on the network_url

    When connecting to a public ethereum network (mainnet or a test net) without
    running a local node requires going through some gateway such as `infura`.

    Using infura has some issues if your code is relying on evm events.
    To use events with an infura connection you have to use the websocket interface.

    Make sure the `infura` url for websocket connection has the following format
    wss://rinkeby.infura.io/ws/v3/357f2fe737db4304bd2f7285c5602d0d
    Note the `/ws/` in the middle and the `wss` protocol in the beginning.

    A note about using the `rinkeby` testnet:
        Web3 py has an issue when making some requests to `rinkeby`
        - the issue is described here: https://github.com/ethereum/web3.py/issues/549
        - and the fix is here: https://web3py.readthedocs.io/en/latest/middleware.html#geth-style-proof-of-authority

    :param network_url:
    :return:
    """
    if network_url == 'ganache':
        network_url = GANACHE_URL

    if network_url.startswith('http'):
        provider = CustomHTTPProvider(network_url)
        
    else:
        if not network_url.startswith('ws'):
            assert network_url in SUPPORTED_NETWORK_NAMES, \
                f'The given network_url *{network_url}* does not start with either ' \
                f'`http` or `wss`, in this case a network name is expected and must ' \
                f'be one of the supported networks {SUPPORTED_NETWORK_NAMES}.'

            network_url = get_infura_url(WEB3_INFURA_PROJECT_ID, network_url)

        provider = WebsocketProvider(network_url)

    return provider


def get_contracts_addresses(network, config):
    return ContractHandler.get_contracts_addresses(network, config.address_file)


def to_base_18(amt: float) -> int:
    return to_base(amt, 18)


def to_base(amt: float, dec: int) -> int:
    """returns value in e.g. wei (taking e.g. ETH as input)"""
    return int(amt * 1*10**dec)
       

def from_base_18(num_base: int) -> float:
    return from_base(num_base, 18)


def from_base(num_base: int, dec: int) -> float:
    """returns value in e.g. ETH (taking e.g. wei as input)"""
    return float(num_base / (10**dec))


def get_dtfactory_address(network=None):
    return DTFactory.configured_address(
        network or Web3Helper.get_network_name(), ConfigProvider.get_config().address_file
    )


def get_bfactory_address(network=None):
    return BFactory.configured_address(
        network or Web3Helper.get_network_name(), ConfigProvider.get_config().address_file
    )


def get_ocean_token_address(network=None):
    addresses = get_contracts_addresses(
        network or Web3Helper.get_network_name(), ConfigProvider.get_config()
    )
    return addresses.get('Ocean') if addresses else None

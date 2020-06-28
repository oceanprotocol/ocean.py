from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider
from web3 import WebsocketProvider

WEB3_INFURA_PROJECT_ID = '357f2fe737db4304bd2f7285c5602d0d'

GANACHE_URL = 'http://127.0.0.1:8545'


SUPPORTED_NETWORK_NAMES = {'rinkeby', 'kovan', 'ganache', 'mainnet', 'ropsten'}


def get_infura_url(infura_id, network):
    return f"wss://{network}.infura.io/ws/v3/{infura_id}"


def get_web3_provider(network_url):
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
            assert network_url in SUPPORTED_NETWORK_NAMES

            network_url = get_infura_url(WEB3_INFURA_PROJECT_ID, network_url)

        provider = WebsocketProvider(network_url)

    return provider

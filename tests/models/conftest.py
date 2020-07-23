import pytest

from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dt_factory import DTFactory
from ocean_lib.ocean import util
from ocean_lib.ocean.util import get_dtfactory_address, get_sfactory_address, get_OCEAN_address, toBase18
from ocean_lib.web3_internal.account import Account
from ocean_lib.web3_internal.utils import privateKeyToAddress
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.models import btoken
from ocean_lib.web3_internal.web3helper import Web3Helper
from tests.resources.helper_functions import get_web3, get_publisher_wallet, get_ganache_wallet

_NETWORK = "ganache"
HUGEINT = 2 ** 255


@pytest.fixture
def network():
    return _NETWORK


@pytest.fixture
def dtfactory_address():
    return get_dtfactory_address(_NETWORK)


@pytest.fixture
def sfactory_address():
    return get_sfactory_address(_NETWORK)


@pytest.fixture
def OCEAN_address():
    return get_OCEAN_address(_NETWORK)


@pytest.fixture
def alice_private_key():
    return alice_info().private_key


@pytest.fixture
def alice_address():
    return alice_info().address


@pytest.fixture
def alice_wallet():
    return alice_info().wallet


@pytest.fixture
def alice_account():
    return alice_info().account


@pytest.fixture
def alice_ocean():
    return alice_info().ocean


@pytest.fixture
def bob_private_key():
    return bob_info().private_key


@pytest.fixture
def bob_address():
    return bob_info().address


@pytest.fixture
def bob_wallet():
    return bob_info().wallet


@pytest.fixture
def bob_account():
    return bob_info().account


@pytest.fixture
def bob_ocean():
    return bob_info().ocean


@pytest.fixture
def T1():  # 'TOK1' with 1000.0 held by Alice
    return alice_info().T1


@pytest.fixture
def T2():  # 'TOK2' with 1000.0 held by Alice
    return alice_info().T2


def alice_info():
    return make_info('Alice', 'TEST_PRIVATE_KEY1')


def bob_info():
    return make_info('Bob', 'TEST_PRIVATE_KEY2')


def make_info(name, private_key_name):
    # assume that this account has ETH with gas.
    class _Info:
        pass

    info = _Info()
    web3 = get_web3()

    info.web3 = web3

    info.private_key = util.confFileValue(_NETWORK, private_key_name)
    info.address = privateKeyToAddress(info.private_key)
    info.account = Account(private_key=info.private_key)
    info.wallet = Wallet(web3, private_key=info.private_key)
    config = {'network': _NETWORK,
              'privateKey': info.private_key,
              'address.file': 'artifacts/addresses.json',
              }

    wallet = get_ganache_wallet()
    if wallet:
        assert Web3Helper.from_wei(Web3Helper.get_ether_balance(wallet.address)) > 4
        if Web3Helper.from_wei(Web3Helper.get_ether_balance(info.address)) < 2:
            Web3Helper.send_ether(wallet, info.address, 4)

    from ocean_lib.ocean import Ocean
    info.ocean = Ocean(config)
    info.T1 = _deployAndMintToken('TOK1', info.address)
    info.T2 = _deployAndMintToken('TOK2', info.address)

    return info


def _deployAndMintToken(symbol: str, to_address: str) -> btoken.BToken:
    wallet = get_ganache_wallet()
    dt_address = DataToken.deploy(
        wallet.web3, wallet.address, None,
        'Template Contract', 'TEMPLATE', wallet.address, DTFactory.CAP, DTFactory.FIRST_BLOB
    )
    dt_factory = DTFactory(DTFactory.deploy(wallet.web3, wallet.address, None, dt_address))
    token_address = dt_factory.get_token_address(dt_factory.createToken(symbol, wallet))
    token = DataToken(token_address)
    token.mint(to_address, toBase18(1000), wallet)

    return btoken.BToken(token.address)

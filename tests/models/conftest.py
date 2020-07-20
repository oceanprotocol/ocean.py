import brownie
import pytest

from ocean_lib.ocean import constants #import here to toggle type-checking
from ocean_lib import Ocean
from ocean_lib.ocean import util
from ocean_lib.web3_internal.account import Account
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.models import btoken

from tests.resources.helper_functions import brownieAccount
    
_NETWORK = "ganache"
HUGEINT = 2**255
_BROWNIE_PROJECT = brownie.project.load(f'./', name=f'MyProject')

@pytest.fixture
def network():
    return _NETWORK

@pytest.fixture
def brownie_project():
    return _BROWNIE_PROJECT

@pytest.fixture
def dtfactory_address():
    return _dtfactory_address()

@pytest.fixture
def sfactory_address():
    return _sfactory_address()

@pytest.fixture
def OCEAN_address():
    return _OCEAN_address()

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
def T1():  #'TOK1' with 1000.0 held by Alice
    return alice_info().T1

@pytest.fixture
def T2():  #'TOK2' with 1000.0 held by Alice
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
    web3 = brownie.network.web3
    
    info.web3 = web3
    info.brownie_project = _BROWNIE_PROJECT
    
    info.private_key = util.confFileValue(_NETWORK, private_key_name)
    info.address = util.privateKeyToAddress(info.private_key)
    info.account = Account(private_key=info.private_key)
    info.wallet = Wallet(web3, key=info.private_key)
    config = {'network': _NETWORK,
              'privateKey': info.private_key,
              'dtfactory.address': _dtfactory_address(),
              'sfactory.address': _sfactory_address(),
              'OCEAN.address': _OCEAN_address(),
    }
    info.ocean = Ocean(config)
    info.T1 = _deployAndMintToken('TOK1', info.address)
    info.T2 = _deployAndMintToken('TOK2', info.address)    

    return info

def _deployAndMintToken(symbol: str, to_address: str) -> btoken.BToken:
    p = _BROWNIE_PROJECT
    private_key = util.confFileValue(_NETWORK, 'FACTORY_DEPLOYER_PRIVATE_KEY')
    account = brownieAccount(private_key)
    token = p.DataTokenTemplate.deploy(
        symbol, symbol, account.address, HUGEINT, '',
        {'from': account})
    
    token.mint(to_address, util.toBase18(1000.0), {'from': account})
    
    return btoken.BToken(brownie.network.web3, token.address)

def _dtfactory_address():
    return util.confFileValue(_NETWORK, 'DTFACTORY_ADDRESS')

def _sfactory_address():
    return util.confFileValue(_NETWORK, 'SFACTORY_ADDRESS')

def _OCEAN_address():
    return util.confFileValue(_NETWORK, 'OCEAN_ADDRESS')

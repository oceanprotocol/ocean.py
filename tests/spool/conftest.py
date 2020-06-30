import brownie
import pytest

from ocean_lib.ocean import constants #import here to toggle type-checking
from ocean_lib import Ocean
from ocean_lib.ocean import util
from ocean_lib.spool_py import BToken

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
def OCEAN_address():
    return util.confFileValue(_NETWORK, 'OCEAN_ADDRESS')

def dtfactory_address():
    return util.confFileValue(_NETWORK, 'DTFACTORY_ADDRESS')

def alice_info():
    return make_info('Alice', 'TEST_PRIVATE_KEY1')

def bob_info():
    return make_info('Bob', 'TEST_PRIVATE_KEY2')

def make_info(name, private_key_name):
    # assume that this account has ETH with gas.
    class _Info:
        pass
    info = _Info()
    info.private_key = util.confFileValue(_NETWORK, private_key_name)
    info.address = util.privateKeyToAddress(info.private_key)
    info.context = util.Context(_NETWORK, private_key=info.private_key)
    info.context.brownie_project = _BROWNIE_PROJECT
    info.view = util.AccountView(_NETWORK, info.address, name)
    info.config = {'network': _NETWORK,
                   'privateKey': info.private_key,
                   'dtfactory.address': dtfactory_address()}
    info.ocean = Ocean(info.config)
    return info

@pytest.fixture
def alice_private_key():
    return alice_info().private_key

@pytest.fixture
def alice_address():
    return alice_info().address

@pytest.fixture
def alice_context():
    return alice_info().context

@pytest.fixture
def alice_view():
    return alice_info().view

@pytest.fixture
def alice_config():
    return alice_info().config

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
def bob_context():
    return bob_info().context

@pytest.fixture
def bob_view():
    return bob_info().view

@pytest.fixture
def bob_config():
    return bob_info().config

@pytest.fixture
def bob_ocean():
    return bob_info().ocean


@pytest.fixture
def brownie_account():
    return brownie_info().account

@pytest.fixture
def brownie_token1():
    return brownie_info().token1

@pytest.fixture
def brownie_token2():
    return brownie_info().token2

@pytest.fixture
def T1(): #'TOK1' with 1000.0 minted by Alice
    c = make_info('Alice', 'TEST_PRIVATE_KEY1').context
    token_address = brownie_info().token1.address
    return BToken.BToken(c, token_address)

@pytest.fixture
def T2():  #'TOK2' with 1000.0 minted by Alice
    c = make_info('Alice', 'TEST_PRIVATE_KEY1').context
    token_address = brownie_info().token2.address
    return BToken.BToken(c, token_address)

@pytest.fixture
def brownie_sfactory():
    return brownie_info().sfactory

@pytest.fixture
def brownie_spool():
    return brownie_info().spool

def brownie_info():
    web3 = brownie.network.web3
    private_key = util.confFileValue('ganache', 'FACTORY_DEPLOYER_PRIVATE_KEY')
    account = brownieAccount(private_key)
    p = _BROWNIE_PROJECT
    
    token1 = p.DataTokenTemplate.deploy('token1', 'TOK1', account.address, HUGEINT, '', {'from': account})
    token2 = p.DataTokenTemplate.deploy('token2', 'TOK2', account.address, HUGEINT, '', {'from': account})

    token1.mint(account.address, util.toBase18(1000.0))
    token2.mint(account.address, util.toBase18(1000.0))

    spool_template = p.SPool.deploy({'from': account})
    
    sfactory = p.SFactory.deploy(spool_template.address, {'from': account})
    
    tx = sfactory.newSPool(account.address, {'from': account}) 
    spool1_address = tx.events['SPoolCreated']['newSPoolAddress']
    spool1 = brownie.Contract.from_abi("SPool", spool1_address, abi=spool_template.abi)
    
    class _BrownieInfo:
        pass
    bi = _BrownieInfo()
    bi.account = account
    bi.token1 = token1
    bi.token2 = token2
    bi.sfactory = sfactory
    bi.spool = spool1
    return bi

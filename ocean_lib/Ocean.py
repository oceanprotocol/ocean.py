#do *not* import brownie, that's too much dependency here
import configparser
import eth_account
import json
import os
from web3 import Web3

from . import constants

class Ocean:
    def __init__(self, config):
        self._network = config['network']
        if self._network == 'development': 
            network_url = confFileValue(self._network, 'GANACHE_URL')
        else:
            raise NotImplementedError(self._network)
        self._web3 = Web3(Web3.HTTPProvider(network_url))
            
        self._private_key = config['privateKey']
        self._web3.eth.defaultAccount = privateKeyToAddress(self._private_key)
        
        self._factory = _Factory(self._network, self._web3)
        
    def createDatatoken(self, blob):
        return self._factory.createDatatoken(blob)

    def getAsset(self, address):
        raise NotImplementedError()     
        
class _Factory:
    def __init__(self, network, web3):
        self._web3 = web3
        
        addr = confFileValue(network, 'FACTORY_ADDRESS')
        abi = self._abi()
        self._contract = web3.eth.contract(address=addr, abi=abi)
        
    def createDatatoken(self, blob):
        name = "Test Token" #FIXME: make random
        symbol = "TST"      #""
        cap = constants.DEFAULT_MINTING_CAP
        minter = self._web3.eth.defaultAccount
        
        tx_hash = self._contract.functions.createToken(name, symbol, cap, blob, minter).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

        #set token_addr. FIXME. How js unit tests do it:
        #  grab eventEmitted 'ev', then token_address = ev.param1
        token_addr = FIXME
        token = DataToken(token_addr)
        return token
    
    def _abi(self):
        filename = './build/contracts/Factory.json' #FIXME magic number
        return _abi(filename)
        
class DataToken:
    def __init__(self, token_addr, web3):
        self._address = token_addr
        self._web3 = web3
        
        abi = self._abi()
        token = web3.eth.contract(address=token_addr, abi=abi)
        self._contract = web3.eth.contract(address=token_addr, abi=abi)

    def getAddress(self):
        return self._address

    def mint(self, value):
        account = self._web3.eth.defaultAccount
        tx_hash = self._contract.functions.mint(account, value).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        
    def transfer(self, recipient, amount):
        tx_hash = self._contract.functions.transfer(recipient, amount).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    def _abi(self):
        filename = './build/contracts/ERC20Template.json' #FIXME magic number
        return _abi(filename)

class Asset:
    def __init__(self):
        pass

    def download(self, address):
        raise NotImplementedError()   
        
def privateKeyToAddress(private_key):
    return privateKeyToAccount(private_key).address

def privateKeyToAccount(private_key):
    return eth_account.Account().from_key(private_key)

def confFileValue(network, key):
    conf = configparser.ConfigParser()
    path = os.path.expanduser(constants.CONF_FILE_PATH)
    conf.read(path)
    return conf[network][key]

def _abi(filename):
    with open(filename, 'r') as f:
        text = f.read()
    abi = json.loads(text)['abi']
    return abi
    

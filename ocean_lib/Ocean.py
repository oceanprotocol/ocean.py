#do *not* import brownie, that's too much dependency here
import configparser
import eth_account
import json
import os
from web3 import Web3

from . import constants
from . import util

class _Context:
    def __init__(self, network, web3, private_key):
        self.network = network
        self.web3 = web3
        self.private_key = private_key
        
        self.account = privateKeyToAccount(private_key)
        self.address = self.account.address

class Ocean:
    def __init__(self, config):
        network = config['network']
        
        if network == 'ganache': 
            network_url = confFileValue('DEFAULT', 'GANACHE_URL')
        else:
            infura_id = confFileValue('DEFAULT', 'WEB3_INFURA_PROJECT_ID')
            network_url = util.getInfuraUrl(infura_id, network)
        web3 = util.web3(network_url)
            
        private_key = config['privateKey']
        
        self._c = _Context(network, web3, private_key)
        self._factory = _Factory(self._c)
        
    def createToken(self, blob):
        return self._factory.createToken(blob)

    def getToken(self, token_addr):
        return DataToken(self._c, token_addr)
        
class _Factory:
    def __init__(self, c: _Context):
        self._c: _Context = c
        
        factory_addr = confFileValue(c.network, 'FACTORY_ADDRESS')
        factory_abi = self._abi()
        self._factory_contract = c.web3.eth.contract(
            address=factory_addr, abi=factory_abi)
        
    def createToken(self, blob):
        #set function
        name, symbol = "Test Token", "TST" #FIXME make random
        cap = constants.DEFAULT_MINTING_CAP
        minter = self._c.address
        function = self._factory_contract.functions.createToken(
            name, symbol, cap, blob, minter)

        #build and send tx
        print("==Build & send tx for createToken()")
        gas_limit = constants.DEFAULT_GAS_LIMIT__CREATE_TOKEN
        (tx_hash, tx_receipt) = _buildAndSendTx(self._c, function, gas_limit)

        #grab token_addr
        print("==Grab token address")
        token_addr = self._factory_contract.functions.getTokenAddress(symbol).call()
        print(f"==token_addr={token_addr}")

        #compute return object
        token = DataToken(self._c, token_addr)
        return token
    
    def _abi(self):
        filename = f'./abi/Factory.json' 
        return _abi(filename)
        
class DataToken:
    def __init__(self, c: _Context, token_addr):
        self._c: _Context = c
        self._token_address = token_addr
        
        token_abi = self._abi()
        self._token_contract = c.web3.eth.contract(
            address=token_addr, abi=token_abi)

    def getAddress(self):
        return self._token_address

    def mint(self, num_tokens):
        #set function
        function = self._token_contract.functions.mint(
            self._c.address, num_tokens)

        #build and send tx
        print("==Build & send tx for mint()")
        gas_limit = constants.DEFAULT_GAS_LIMIT__MINT_TOKENS
        gas_price = int(confFileValue(self._c.network, 'GAS_PRICE'))
        max_fees_wei = gas_limit * gas_price
        (tx_hash, tx_receipt) = _buildAndSendTx(
            self._c, function, gas_limit, max_fees_wei)
        
    def transfer(self, recipient_addr, num_tokens):
        #set function
        function = self._token_contract.functions.transfer(
            recipient_addr, num_tokens)

        #build and send tx
        print("==Build & send tx for transfer()")
        gas_limit = constants.DEFAULT_GAS_LIMIT__TRANSFER_TOKENS
        (tx_hash, tx_receipt) = _buildAndSendTx(self._c, function, gas_limit)

    def download(self):
        print("FIXME need to implement when provider-py is ready")
        
    def _abi(self):
        filename = f'./abi/DataTokenTemplate.json' 
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
    
def _buildAndSendTx(c: _Context, function, gas_limit, num_wei=0):
    nonce = c.web3.eth.getTransactionCount(c.address)
    gas_price = int(confFileValue(c.network, 'GAS_PRICE'))
    tx_params = { 
        "from": c.address,
        "value": num_wei, 
        "nonce": nonce,
        "gas": gas_limit,
        "gasPrice": gas_price,
    }

    tx = function.buildTransaction(tx_params)
    signed_tx = c.web3.eth.account.sign_transaction(tx, private_key=c.private_key)
    try: 
        tx_hash = c.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    except ValueError as err:
        print(f"Error: {err}")
        import pdb; pdb.set_trace()

    tx_receipt = c.web3.eth.waitForTransactionReceipt(tx_hash)
    print(f"tx_receipt={tx_receipt}")
    print("Tx has completed.")
    if tx_receipt['status'] == 0: #did tx fail?
        print("Eek, the tx failed")
        import pdb; pdb.set_trace()
    return (tx_hash, tx_receipt)

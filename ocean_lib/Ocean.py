#do *not* import brownie, that's too much dependency here
import configparser
import eth_account
import json
import os
from web3 import Web3

from . import constants

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
        if network == 'development': 
            network_url = confFileValue(network, 'GANACHE_URL')
        else:
            raise NotImplementedError(network)
        web3 = Web3(Web3.HTTPProvider(network_url))
            
        private_key = config['privateKey']
        
        c = _Context(network, web3, private_key)
        self._factory = _Factory(c)
        
    def createToken(self, blob):
        return self._factory.createToken(blob)

    def getAsset(self, address):
        raise NotImplementedError()     
        
class _Factory:
    def __init__(self, c: _Context):
        self._c: _Context = c
        
        factory_addr = confFileValue(c.network, 'FACTORY_ADDRESS')
        factory_abi = self._abi()
        self._factory_contract = c.web3.eth.contract(
            address=factory_addr, abi=factory_abi)
        
    def createToken(self, blob):
        print("==createToken: start")
        #set function
        name, symbol = "Test Token", "TST" #FIXME make random
        cap = constants.DEFAULT_MINTING_CAP
        minter = self._c.address
        function = self._factory_contract.functions.createToken(
            name, symbol, cap, blob, minter)

        #build and send tx
        gas_limit = constants.DEFAULT_GAS_LIMIT__CREATE_TOKEN
        import pdb; pdb.set_trace()
        (tx_hash, tx_receipt) = _buildAndSendTx(self._c, function, gas_limit)

        #grab token_addr
        events = self._factory_contract.events #web3.contract.ContractEvents object
        event = events.TokenCreated() #web3._utils.datatypes.TokenCreated object
        
        #event_filter = events.TokenCreated.createFilter(fromBlock=0)
        #entries = event_filter.get_new_entries()

        #**the problem: tx_receipt['logs'] = []. Then I have no data to grab logs from.
        # Similar: tx_receipt.logs = []
        ##logs = events.TokenCreated.processReceipt(tx_receipt)
        
        #processReceipt() calls _parse_logs() which has a bug!
        #TypeError: _parse_logs() missing 1 required positional argument: 'errors'
        #workaround: it uses web3._utils.events.get_event_data(), so we
        # will simply use that directly, following the pattern of
        # how _parse_logs() uses it
        from web3._utils.events import get_event_data
        log = tx_receipt['logs']
        contract = self._factory_contract
        event_abi = event._get_event_abi()
        import pdb; pdb.set_trace()
        rich_log = get_event_data(contract.web3.codec, event_abi, log)
        
        #log = tx_receipt['logs'][0]
        import pdb; pdb.set_trace()
        token_addr = FIXME

        #compute return object
        token = _DataToken(self._c, token_addr)
        print("==createToken: done")
        return token
    
    def _abi(self):
        #FIXME: don't rely on brownie output directory 'build/contracts'
        filename = './build/contracts/Factory.json' 
        return _abi(filename)
        
class DataToken:
    def __init__(self, c: _Context, token_addr):
        self._c: _Context = c
        self._token_address = token_addr
        
        token_abi = self._abi()
        self._token_contract = web3.eth.contract(
            address=token_addr, abi=token_abi)

    def getAddress(self):
        return self._token_address

    def mint(self, num_tokens):
        #set function
        function = self._token_contract.functions.mint(
            self._c.account, num_tokens)

        #build and send tx
        gas_limit = constants.DEFAULT_GAS_LIMIT__MINT_TOKENS
        (tx_hash, tx_receipt) = _buildAndSendTx(self._c, function, gas_limit)
        
    def transfer(self, recipient_addr, num_tokens):
        #set function
        function = self._contract.functions.transfer(
            recipient_addr, num_tokens)

        #build and send tx
        gas_limit = constants.DEFAULT_GAS_LIMIT__TRANSFER_TOKENS
        (tx_hash, tx_receipt) = _buildAndSendTx(self._c, function, gas_limit)

    def _abi(self):
        #FIXME: don't rely on brownie output directory 'build/contracts'
        filename = './build/contracts/DataTokenTemplate.json' 
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
    
def _buildAndSendTx(c: _Context, function, gas_limit, num_eth=0):
    print("==_buildAndSendTx: begin")
    tx_params = { 
        "from": c.address,
        "gas": constants.DEFAULT_GAS_LIMIT__TRANSFER_TOKENS,
        "value": num_eth, 
        "nonce": c.web3.eth.getTransactionCount(c.address),
    }

    tx = function.buildTransaction(tx_params)
    signed_tx = c.web3.eth.account.sign_transaction(tx, private_key=c.private_key)
    tx_hash = c.web3.eth.sendRawTransaction(signed_tx.rawTransaction) 
    print(f"Sent raw transaction. tx_hash={c.web3.toHex(tx_hash)}")

    tx_receipt = c.web3.eth.waitForTransactionReceipt(tx_hash)
    print(f"tx_receipt={tx_receipt}")
    print("Tx has completed.")
    if tx_receipt['status'] == 0: #did tx fail?
        print("Eek, the tx failed")
        import pdb; pdb.set_trace()
    print(f"==_buildAndSendTx: done. tx_hash={tx_hash}")
    return (tx_hash, tx_receipt)

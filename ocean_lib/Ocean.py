#do *not* import brownie, that's too much dependency here
import configparser
import eth_account 
import os

class Ocean:
    def __init__(self, config):
        self._network = config['network']
        self._private_key = config['privateKey']
        
        cp = configparser.ConfigParser()
        cp.read(os.path.expanduser('~/ocean.conf'))
        factory_addr = cp[self._network]['FACTORY_ADDRESS']
        self._factory = Factory(factory_addr)
        
    def createDatatoken(self, blob):
        """@return -- brownie-style datatoken contract"""
        account = privateKeyToAccount(self._private_key)
        tx = self._factory.createToken("TST", "Test Token", account)
        token_addr = self._factory.currentTokenAddress()
        token = Contract.from_abi("Token", token_addr, ERC20.abi)
        # FIXME: add blob
        return token

class Factory:
    def __init__(self, factory_addr):
        pass

def privateKeyToAddress(private_key):
    return account(private_key).address

def privateKeyToAccount(private_key):
    return eth_account.Account().from_key(private_key)

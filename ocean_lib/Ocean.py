import brownie
from brownie import Contract, ERC20
import eth_account 

class Ocean:
    def __init__(self, config, factory):
        network  = config['network']
        if not brownie.network.is_connected():
            brownie.network.connect(network)

        private_key = config['privateKey']
        self._account = account(private_key)

        self._factory = factory
        
    def createDatatoken(self, blob):
        """@return -- brownie-style datatoken contract"""
        tx = self._factory.createToken("TST", "Test Token", self._account)
        token_addr = self._factory.currentTokenAddress()
        token = Contract.from_abi("Token", token_addr, ERC20.abi)
        # FIXME: add blob
        return token

def account(private_key):
    assert brownie.network.is_connected()
    return brownie.network.accounts.add(priv_key=private_key)

def address(private_key):
    return eth_account.Account().privateKeyToAccount(private_key).address

import brownie
import configparser
import enforce
import eth_account
import json
import os
import typing
from web3 import Web3, WebsocketProvider

from ocean_lib.web3_internal.account import privateKeyToAddress
from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider

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

@enforce.runtime_validation
def toBase18(amt: float) -> int:
    return toBase(amt, 18)

@enforce.runtime_validation
def toBase(amt: float, dec: int) -> int:
    """returns value in e.g. wei (taking e.g. ETH as input)"""
    return int(amt * 1*10**dec)
       
@enforce.runtime_validation
def fromBase18(num_base: int) -> float:
    return fromBase(num_base, 18)

@enforce.runtime_validation
def fromBase(num_base: int, dec: int) -> float:
    """returns value in e.g. ETH (taking e.g. wei as input)"""
    return float(num_base / (10**dec))

def brownie_account(private_key):
    assert brownie.network.is_connected()
    return brownie.network.accounts.add(private_key=private_key)

#FIXME: deprecate this
CONF_FILE_PATH = '~/ocean.conf'
@enforce.runtime_validation
def confFileValue(network: str, key: str) -> str:
    conf = configparser.ConfigParser()
    path = os.path.expanduser(CONF_FILE_PATH)
    conf.read(path)
    return conf[network][key]

#FIXME: deprecate this
@enforce.runtime_validation
class Context:
    def __init__(self, network: str,
                 web3=None,
                 address:typing.Union[str,None]=None,
                 private_key:typing.Union[str,None]=None):
        assert not isinstance(web3, str)
        self.network = network
        self.web3 = web3
        self.private_key = private_key
        self.address = address
        if web3 is None:
            self.web3 = Web3(get_web3_provider(network))
        if private_key is not None:
            self.address = privateKeyToAddress(private_key)
        self.brownie_project = None

#FIXME: maybe deprecate this
@enforce.runtime_validation
class AccountView:
    def __init__(self, network: str, address: str, descr_s: str):
        self._c = Context(network, address=address)
        self._descr_s = descr_s #e.g. "Alice"
        self.dt_address = None
        self.pool_address = None

    def __str__(self) -> str:
        s = []
        s += [f"Balances for {self._descr_s}:"]
        s += [self.ETHstr()]
        s += [self.OCEANstr()]
        if self.dt_address is not None:
            s += [self.DTstr()]
        if self.pool_address is not None:
            s += [self.BPTstr()]
        s += [""]
        return "\n".join(s)
    
    def ETHstr(self) -> str:
        return f"  {self.ETH()} ETH ({self.ETH_base()} base, aka wei)"

    def ETH(self) -> float:
        """Balance of ETH, in units of ETH (not wei)"""
        return fromBase18(self.ETH_base())

    def ETH_base(self) -> int:
        """Balance of ETH, in units of its base (wei)"""
        return self._c.web3.eth.getBalance(self._c.address) 

    def OCEANstr(self) -> str:
        return f"  {self.OCEAN()} OCEAN ({self.OCEAN_base()} base)"

    def OCEAN(self) -> float:
        """Balance of OCEAN, in units of OCEAN"""
        OCEAN_base = self.OCEAN_base()
        return fromBase18(OCEAN_base)
    
    def OCEAN_base(self) -> int:
        """Balance of OCEAN, in units of its base"""
        token_address = confFileValue(self._c.network, 'OCEAN_ADDRESS')
        return tokenBalance_base(self._c.network, self._c.address, token_address)        
    def DTstr(self) -> str:
        return f"  {self.DT()} DT ({self.DT_base()} base)"

    def DT(self) -> float:
        """Balance of data token, in units of that token (not its base)"""
        return fromBase18(self.DT_base())

    def DT_base(self) -> int:
        """Balance of data token, in units of its base"""
        return tokenBalance_base(
            self._c.network, self._c.address, self.dt_address)
        
    def BPTstr(self) -> str:
        return f"  {self.BPT()} BPT ({self.BPT_base()} base)"

    def BPT(self) -> float:
        """Balance of balancer pool token, in units of that token (not base)"""
        return fromBase18(self.BPT_base())

    def BPT_base(self) -> int:
        """Balance of data token, in units of its base"""
        return tokenBalance_base(
            self._c.network, self._c.address, self.pool_address)

#FIXME: maybe deprecate this
@enforce.runtime_validation
def tokenBalance_base(network: str, balance_address: str, token_address: str) -> int:
    min_abi = [{'constant': True, 'inputs': [{'internalType': 'address', 'name': 'whom', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}], 'payable': False, 'stateMutability': 'view', 'type': 'function'}]
    web3 = Web3(get_web3_provider(network))
    contract = web3.eth.contract(token_address, abi=min_abi)
    func = contract.functions.balanceOf(balance_address)
    return func.call()


#FIXME: maybe deprecate this
# (or deprecate the similar but more complex version in contract_handler)
@enforce.runtime_validation
def abi(filename: str):
    with open(filename, 'r') as f:
        return json.loads(f.read())
    
#FIXME: maybe deprecate this
# (or deprecate the similar functionality in ocean_lib/web3_internal/contract_base.py?)
GASLIMIT_DEFAULT = 5000000 #FIXME: put in better place
@enforce.runtime_validation
def buildAndSendTx(c: Context,
                   function,
                   gaslimit: int = GASLIMIT_DEFAULT,
                   num_wei: int = 0):
    assert isinstance(c.address, str)
    assert isinstance(c.private_key, str)
    
    nonce = c.web3.eth.getTransactionCount(c.address)
    gas_price = int(confFileValue(c.network, 'GAS_PRICE'))
    tx_params = {
        "from": c.address,
        "value": num_wei,
        "nonce": nonce,
        "gas": gaslimit,
        "gasPrice": gas_price,
    }

    tx = function.buildTransaction(tx_params)
    signed_tx = c.web3.eth.account.sign_transaction(tx, private_key=c.private_key)
    tx_hash = c.web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_receipt = c.web3.eth.waitForTransactionReceipt(tx_hash)
    if tx_receipt['status'] == 0:  # did tx fail?
        raise Exception("The tx failed. tx_receipt: {tx_receipt}")
    return (tx_hash, tx_receipt)
    

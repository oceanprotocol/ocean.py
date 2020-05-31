from eth_account import Account
import eth_keys
import eth_utils
from web3 import Web3
    
def getInfuraUrl(infura_id, network):
    return f"https://{network}.infura.io/v3/{infura_id}"

def web3(url):
    return Web3(Web3.HTTPProvider(url))

def printAccountInfo(web3, account_descr_s, private_key):
    print(f"Account {account_descr_s}:")
    print(f"  private key: {private_key}")

    private_key_bytes = eth_utils.decode_hex(private_key)
    private_key_object = eth_keys.keys.PrivateKey(private_key_bytes)
    public_key = private_key_object.public_key
    print(f"  public key: {public_key}")
    
    account = Account().privateKeyToAccount(private_key)
    print(f"  address: {account.address}")
    
    balance_wei = web3.eth.getBalance(account.address)
    balance_eth = web3.fromWei(balance_wei, 'ether')
    print(f"  balance: {balance_wei} Wei ({balance_eth} Ether)")

def printAccountsInfo(web3, private_keys):
    for i, private_key in enumerate(private_keys):
        account_descr_s = str(i+1)
        printAccountInfo(web3, account_descr_s, private_key)

import enforce
import warnings

from ocean_lib.models.datatoken import DataToken
from ocean_lib.ocean import util
from ocean_lib.web3_internal.wallet import Wallet

@enforce.runtime_validation
class DTFactory:
    def __init__(self, web3, contract_address: str):
        self.web3 = web3
        abi = self._abi()
        self.contract = web3.eth.contract(contract_address, abi=abi)
        
    @property
    def address(self):
        return self.contract.address
    
    def _abi(self):
        return util.abi(filename='./abi/DTFactory.abi')
    
    #============================================================
    #reflect DTFactory Solidity methods
    def createToken(self, blob: str, from_wallet: Wallet) -> str:
        f = self.contract.functions.createToken(blob)
        (tx_hash, tx_receipt) = util.buildAndSendTx(f, from_wallet)

        warnings.filterwarnings("ignore") #ignore unwarranted warning up next
        rich_logs = getattr(self.contract.events, 'TokenCreated')().processReceipt(tx_receipt)
        token_address = rich_logs[0]['args']['newTokenAddress'] 
        warnings.resetwarnings()

        return token_address

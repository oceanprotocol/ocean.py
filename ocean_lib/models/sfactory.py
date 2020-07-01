import enforce
import warnings

from . import bconstants
from ocean_lib.ocean import util
from ocean_lib.web3_internal.wallet import Wallet
    
@enforce.runtime_validation
class SFactory:    
    def __init__(self, web3, contract_address: str):
        abi = self._abi()
        self.contract = web3.eth.contract(address=contract_address, abi=abi)
    
    def _abi(self):
        return util.abi(filename='./abi/SFactory.abi')
        
    #============================================================
    #reflect SFactory Solidity methods
    def newSPool(self, from_wallet: Wallet) -> str:
        print("SPool.newSPool(). Begin.")
        controller_address = from_wallet.address
        func = self.contract.functions.newSPool(controller_address)
        gaslimit = bconstants.GASLIMIT_SFACTORY_NEWSPOOL
        (_, tx_receipt) = util.buildAndSendTx(func, from_wallet, gaslimit)

        # grab pool_address
        warnings.filterwarnings("ignore") #ignore unwarranted warning up next
        rich_logs = self.contract.events.SPoolCreated().processReceipt(tx_receipt)
        warnings.resetwarnings()
        pool_address = rich_logs[0]['args']['newSPoolAddress']
        print(f"  pool_address = {pool_address}")

        print("SPool.newSPool(). Done.")
        return pool_address

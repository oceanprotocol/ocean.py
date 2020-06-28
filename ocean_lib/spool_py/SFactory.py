import enforce
import warnings
from . import bconstants
from ocean_lib.ocean import util
    
@enforce.runtime_validation
class SFactory:    
    def __init__(self, c: util.Context):
        self._c: util.Context = c
        address = util.confFileValue(c.network, 'SFACTORY_ADDRESS')
        abi = self._abi()
        self.contract = c.web3.eth.contract(address=address, abi=abi)
    
    def _abi(self):
        return util.abi(filename='./abi/SFactory.abi')
        
    #============================================================
    #reflect SFactory Solidity methods
    def newSPool(self, controller_address:str) -> str:
        print("SPool.newSPool(). Begin.")
        func = self.contract.functions.newSPool(controller_address)
        gaslimit = bconstants.GASLIMIT_SFACTORY_NEWSPOOL
        (_, tx_receipt) = util.buildAndSendTx(self._c, func, gaslimit)

        # grab pool_address
        warnings.filterwarnings("ignore") #ignore unwarranted warning up next
        rich_logs = self.contract.events.SPoolCreated().processReceipt(tx_receipt)
        warnings.resetwarnings()
        pool_address = rich_logs[0]['args']['newSPoolAddress']
        print(f"  pool_address = {pool_address}")

        print("SPool.newSPool(). Done.")
        return pool_address

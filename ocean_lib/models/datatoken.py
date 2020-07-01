import enforce

from ocean_lib.models.btoken import BToken
from ocean_lib.ocean import util
from ocean_lib.web3_internal.wallet import Wallet

@enforce.runtime_validation
class DataToken(BToken):
    
    def _abi(self):
        return util.abi(filename='./abi/DataTokenTemplate.abi')
        
    #============================================================
    #reflect DataToken Solidity methods (new ones beyond BToken)
    def blob(self) -> str:
        return self.contract.functions.blob().call()

    def mint(self, account: str, value_base: int, from_wallet: Wallet):
        f = self.contract.functions.mint(account, value_base)
        (tx_hash, tx_receipt) = util.buildAndSendTx(f, from_wallet)        
    
    def setMinter(self, minter: str, from_wallet: Wallet):
        f = self.contract.functions.setMinter(minter)
        (tx_hash, tx_receipt) = util.buildAndSendTx(f, from_wallet)

    

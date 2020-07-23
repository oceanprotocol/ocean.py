
import warnings

from ocean_lib.web3_internal.contract_base import ContractBase
from . import balancer_constants
from ocean_lib.web3_internal.wallet import Wallet
    

class SFactory(ContractBase):
    CONTRACT_NAME = 'SFactory'

    # ============================================================
    # reflect SFactory Solidity methods
    def newSPool(self, from_wallet: Wallet) -> str:
        print("SPool.newSPool(). Begin.")
        tx_id = self.send_transaction(
            'newSPool',
            (),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_SFACTORY_NEWSPOOL}
        )
        tx_receipt = self.get_tx_receipt(tx_id)

        # grab pool_address
        warnings.filterwarnings("ignore")  # ignore unwarranted warning up next
        rich_logs = self.contract.events.SPoolCreated().processReceipt(tx_receipt)
        warnings.resetwarnings()
        pool_address = rich_logs[0]['args']['newSPoolAddress']
        print(f"  pool_address = {pool_address}")

        print("SPool.newSPool(). Done.")
        return pool_address

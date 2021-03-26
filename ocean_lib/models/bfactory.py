#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings

from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet

from . import balancer_constants


@enforce_types_shim
class BFactory(ContractBase):
    CONTRACT_NAME = "BFactory"

    # ============================================================
    # reflect BFactory Solidity methods
    def newBPool(self, from_wallet: Wallet) -> str:
        print("BPool.newBPool(). Begin.")
        tx_id = self.send_transaction(
            "newBPool",
            (),
            from_wallet,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )
        tx_receipt = self.get_tx_receipt(tx_id)
        if tx_receipt.status != 1:
            raise ValueError(
                f"Create BPool failed: tx_id {tx_id}, tx receipt is {tx_receipt}"
            )

        # grab pool_address
        warnings.filterwarnings("ignore")  # ignore unwarranted warning up next
        rich_logs = self.contract.events.BPoolCreated().processReceipt(tx_receipt)
        warnings.resetwarnings()
        pool_address = rich_logs[0]["args"]["newBPoolAddress"]
        print(f"  pool_address = {pool_address}")

        print("BFactory.newBPool(). Done.")
        return pool_address

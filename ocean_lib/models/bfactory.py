#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet
from web3.logs import DISCARD

from . import balancer_constants


class BFactory(ContractBase):
    CONTRACT_NAME = "BFactory"

    # ============================================================
    # reflect BFactory Solidity methods
    @enforce_types
    def newBPool(self, from_wallet: Wallet, block_confirmations: int) -> str:
        """
        :return: `str` new pool address
        """
        print("BPool.newBPool(). Begin.")
        tx_id = self.send_transaction(
            "newBPool",
            (),
            from_wallet,
            block_confirmations,
            {"gas": balancer_constants.GASLIMIT_BFACTORY_NEWBPOOL},
        )
        tx_receipt = self.get_tx_receipt(self.web3, tx_id)
        if tx_receipt.status != 1:
            raise ValueError(
                f"Create BPool failed: tx_id {tx_id}, tx receipt is {tx_receipt}"
            )

        # grab pool_address
        rich_logs = self.contract.events.BPoolCreated().processReceipt(
            tx_receipt, errors=DISCARD
        )
        pool_address = rich_logs[0]["args"]["newBPoolAddress"]
        print(f"  pool_address = {pool_address}")

        print("BFactory.newBPool(). Done.")
        return pool_address

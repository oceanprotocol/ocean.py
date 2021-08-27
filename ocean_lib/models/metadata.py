#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
from typing import Optional

from enforce_typing import enforce_types
from eth_utils import remove_0x_prefix
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet
from web3.datastructures import AttributeDict


class MetadataContract(ContractBase):
    CONTRACT_NAME = "Metadata"
    EVENT_METADATA_CREATED = "MetadataCreated"
    EVENT_METADATA_UPDATED = "MetadataUpdated"

    @property
    @enforce_types
    def event_MetadataCreated(self):
        return self.events.MetadataCreated()

    @property
    @enforce_types
    def event_MetadataUpdated(self):
        return self.events.MetadataUpdated()

    def get_event_log(
        self, event_name: str, block: int, did: str, timeout: int = 45
    ) -> Optional[AttributeDict]:
        """
        :return: Log if event is found else None
        """
        did = remove_0x_prefix(did)
        start = time.time()
        event = getattr(self.events, event_name)
        logs = []
        while not logs:
            logs = ContractBase.getLogs(event(), fromBlock=block)
            if not logs:
                time.sleep(0.2)

            if time.time() - start > timeout:
                break

        if not logs:
            return None

        _log = None
        for log in logs:
            if remove_0x_prefix(log.args.dataToken) == did:
                _log = log
                break
        return _log

    @enforce_types
    def verify_tx(self, tx_hash: str) -> bool:
        """
        :return bool:
        """
        return self.get_tx_receipt(self.web3, tx_hash).status == 1

    @enforce_types
    def create(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        """
        :return str: hex str transaction hash
        """
        return self.send_transaction("create", (did, flags, data), from_wallet)

    @enforce_types
    def update(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        """
        :return str: hex str transaction hash
        """
        return self.send_transaction("update", (did, flags, data), from_wallet)

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time

from eth_utils import remove_0x_prefix
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types_shim
class MetadataContract(ContractBase):
    CONTRACT_NAME = "Metadata"
    EVENT_METADATA_CREATED = "MetadataCreated"
    EVENT_METADATA_UPDATED = "MetadataUpdated"

    @property
    def event_MetadataCreated(self):
        return getattr(self.events, self.EVENT_METADATA_CREATED)()

    @property
    def event_MetadataUpdated(self):
        return getattr(self.events, self.EVENT_METADATA_UPDATED)()

    def get_event_log(self, event_name, block, did, timeout=45):
        did = remove_0x_prefix(did)
        start = time.time()
        f = getattr(self.events, event_name)().createFilter(fromBlock=block)
        logs = []
        while not logs:
            logs = f.get_all_entries()
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

    def verify_tx(self, tx_hash: str) -> bool:
        return self.get_tx_receipt(tx_hash).status == 1

    def create(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("create", (did, flags, data), from_wallet)

    def update(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("update", (did, flags, data), from_wallet)

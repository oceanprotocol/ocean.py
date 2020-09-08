import time

from eth_utils import remove_0x_prefix

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class DDOContract(ContractBase):
    CONTRACT_NAME = 'DDO'
    EVENT_DDO_CREATED = 'DDOCreated'
    EVENT_DDO_UPDATED = 'DDOCreated'
    EVENT_OWNERSHIP_TRANSFERRED = 'DDOOwnershipTransferred'

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
            if log.args.did.hex() == did:
                _log = log
                break
        return _log

    def verify_tx(self, tx_hash: str) -> bool:
        return self.get_tx_receipt(tx_hash).status == 1

    def didOwner(self, did: str) -> str:
        return self.contract_concise.didOwners(did)

    def create(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction('create', (did, flags, data), from_wallet)

    def update(self, did: str, flags: bytes, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction('update', (did, flags, data), from_wallet)

    def transferOwnership(self, did: str, owner: str, from_wallet: Wallet) -> str:
        return self.send_transaction('transferOwnership', (did, owner), from_wallet)

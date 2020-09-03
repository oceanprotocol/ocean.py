from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class DDOContract(ContractBase):
    CONTRACT_NAME = 'DDO'

    def verify_tx(self, tx_hash: str) -> bool:
        return self.get_tx_receipt(tx_hash).status == 1

    def didOwner(self, did: str) -> str:
        return self.contract_concise.didOwners(did)

    def create(self, did: str, flags: str, data: str, from_wallet: Wallet) -> str:
        return self.send_transaction('create', (did, flags, data), from_wallet)

    def update(self, did: str, flags: str, data: str, from_wallet: Wallet) -> str:
        return self.send_transaction('update', (did, flags, data), from_wallet)

    def transferOwnership(self, did: str, owner: str, from_wallet: Wallet) -> str:
        return self.send_transaction('transferOwnership', (did, owner), from_wallet)

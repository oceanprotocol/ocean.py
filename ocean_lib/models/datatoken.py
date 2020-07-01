import enforce
import os

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.btoken import BToken
from ocean_lib.ocean import util
from ocean_lib.web3_internal.wallet import Wallet
from ocean_utils.http_requests.requests_session import get_requests_session

@enforce.runtime_validation
class DataToken(BToken):
    
    def _abi(self):
        return util.abi(filename='./abi/DataTokenTemplate.abi')

    def download(self, tx_id: str, destination_folder: str,
                 consumer_address: str) -> str:
        url = self.blob()
        download_url = (
            f'{url}?'
            f'consumerAddress={consumer_address}'
            f'&tokenAddress={self.address}'
            f'&transferTxId={tx_id}'
        )
        response = get_requests_session().get(download_url, stream=True)
        file_name = f'file-{self.address}'
        DataServiceProvider.write_file(response, destination_folder, file_name)
        return os.path.join(destination_folder, file_name)
        
    #============================================================
    #reflect DataToken Solidity methods (new ones beyond BToken)
    def blob(self) -> str:
        return self.contract.functions.blob().call()

    def mint(self, account: str, value_base: int, from_wallet: Wallet):
        f = self.contract.functions.mint(account, value_base)
        return util.buildAndSendTx(f, from_wallet)        
    
    def setMinter(self, minter: str, from_wallet: Wallet):
        f = self.contract.functions.setMinter(minter)
        return util.buildAndSendTx(f, from_wallet)

    

from ocean_lib.models.datatoken import DataToken
from ocean_lib.web3_stuff import ContractBase


class FactoryContract(ContractBase):
    @property
    def contract_name(self):
        return 'Factory'

    def create_data_token(self, account, metadata_url):
        tx_hash = self.send_transaction(
            'createToken',
            (metadata_url,),
            transact={'from': account.address,
                      'passphrase': account.password,
                      'account_key': account.key},
        )
        tx_receipt = self.get_tx_receipt(tx_hash)
        logs = getattr(self.events, 'TokenRegistered')().processReceipt(tx_receipt)
        # event_log = self.get_token_registered_event(
        #     tx_receipt.blockNumber,
        #     metadata_url,
        #     account.address
        # )
        if not logs:
            return None

        return DataToken(logs[0].args.tokenAddress)

    def get_token_registered_event(self, block_number, metadata_url, sender):
        event = getattr(self.events, 'TokenRegistered')
        filter_params = {}
        event_filter = event().createFilter(
            fromBlock=block_number,
            toBlock=block_number,
            argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        for log in logs:
            if log.args.blob == metadata_url and sender == log.args.RegisteredBy:
                return log

        return None

    def get_token_minter(self, token_address):
        event = getattr(self.events, 'TokenRegistered')
        filter_params = {'tokenAddress': token_address}
        event_filter = event().createFilter(
            fromBlock=0,
            toBlock='latest',
            argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        for log in logs:
            assert log.args.tokenAddress == token_address
            return log.args.RegisteredBy

        return None

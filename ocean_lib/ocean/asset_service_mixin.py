import logging

from ocean_utils.agreements.service_agreement import ServiceAgreement

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.datatokencontract import DataTokenContract


logger = logging.getLogger(__name__)


class AssetServiceMixin:
    @staticmethod
    def initiate_service(asset, service, consumer_account):
        dt_address = asset.as_dictionary()['dataToken']
        sa = ServiceAgreement.from_ddo(service.type, asset)
        initialize_url = DataServiceProvider.get_initialize_endpoint(sa.service_endpoint)
        response = DataServiceProvider.check_service_availability(
            asset.did, initialize_url, consumer_account, sa.index, sa.type, dt_address)
        if not response:
            raise AssertionError('Data service provider or service is not available.')

        num_tokens = int(response['numTokens'])
        receiver = response['to']
        assert dt_address == response['dataToken']
        dt = DataTokenContract(dt_address)
        balance = dt.contract_concise.balanceOf(consumer_account.address)
        if balance < num_tokens:
            raise AssertionError(f'Your token balance {balance} is not sufficient '
                                 f'to execute the requested service. This service '
                                 f'requires {num_tokens} number of tokens.')

        tx_hash = dt.transfer(receiver, num_tokens, consumer_account)
        try:
            return dt.verify_transfer_tx(tx_hash, consumer_account.address, receiver)
        except (AssertionError, Exception) as e:
            msg = (
                f'Downloading asset files failed. The problem is related to '
                f'the transfer of the data tokens required for the download '
                f'service: {e}'
            )
            logger.error(msg)
            raise AssertionError(msg)

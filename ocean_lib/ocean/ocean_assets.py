"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import copy
import json
import logging
import os

from ocean_utils.agreements.service_agreement import ServiceAgreement
from ocean_utils.agreements.service_factory import ServiceDescriptor, ServiceFactory
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.aquarius.aquarius import Aquarius
from ocean_utils.aquarius.aquarius_provider import AquariusProvider
from ocean_utils.aquarius.exceptions import AquariusGenericError
from ocean_utils.ddo.metadata import MetadataMain
from ocean_utils.ddo.public_key_rsa import PUBLIC_KEY_TYPE_RSA
from ocean_utils.did import DID
from ocean_utils.exceptions import (
    OceanDIDAlreadyExist,
)
from ocean_utils.utils.utilities import checksum

from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import OrderRequirements
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.web3_internal.web3helper import Web3Helper
from ocean_lib.ocean.util import to_base_18

logger = logging.getLogger('ocean')


class OceanAssets:
    """Ocean assets class."""

    def __init__(self, config, data_provider):
        self._config = config
        self._aquarius_url = config.aquarius_url
        self._data_provider = data_provider

        downloads_path = os.path.join(os.getcwd(), 'downloads')
        if self._config.has_option('resources', 'downloads.path'):
            downloads_path = self._config.get('resources', 'downloads.path') or downloads_path
        self._downloads_path = downloads_path

    def _get_aquarius(self, url=None) -> Aquarius:
        return AquariusProvider.get_aquarius(url or self._aquarius_url)

    def _process_service_descriptors(self, service_descriptors, metadata, wallet: Wallet) -> list:
        ddo_service_endpoint = self._get_aquarius().get_service_endpoint()

        service_type_to_descriptor = {sd[0]: sd for sd in service_descriptors}
        _service_descriptors = []
        metadata_service_desc = service_type_to_descriptor.pop(
            ServiceTypes.METADATA,
            ServiceDescriptor.metadata_service_descriptor(
                    metadata, ddo_service_endpoint
            )
        )
        _service_descriptors = [metadata_service_desc, ]

        # Always dafault to creating a ServiceTypes.ASSET_ACCESS service if no services are specified
        access_service_descriptor = service_type_to_descriptor.pop(
            ServiceTypes.ASSET_ACCESS,
            ServiceDescriptor.access_service_descriptor(
                self._build_access_service(metadata, to_base_18(1), wallet.address),
                self._data_provider.get_download_endpoint(self._config)
            )
        )
        compute_service_descriptor = service_type_to_descriptor.pop(
            ServiceTypes.CLOUD_COMPUTE,
            None
        )

        if access_service_descriptor:
            _service_descriptors.append(access_service_descriptor)
        if compute_service_descriptor:
            _service_descriptors.append(compute_service_descriptor)

        _service_descriptors.extend(service_type_to_descriptor.values())
        return ServiceFactory.build_services(_service_descriptors)

    def create(self, metadata: dict, publisher_wallet: Wallet,
               service_descriptors: list=None, owner_address: str=None,
               data_token_address: str=None) -> (Asset, None):
        """
        Register an asset on-chain by creating/deploying a DataToken contract
        and in the Metadata store (Aquarius).

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :param publisher_wallet: Wallet of the publisher registering this asset
        :param service_descriptors: list of ServiceDescriptor tuples of length 2.
            The first item must be one of ServiceTypes and the second
            item is a dict of parameters and values required by the service
        :param owner_address: hex str the ethereum address to assign asset ownership to. After
            registering the asset on-chain, the ownership is transferred to this address
        :param data_token_address: hex str the address of the data token smart contract. The new
            asset will be associated with this data token address.
        :return: DDO instance
        """
        assert isinstance(metadata, dict), f'Expected metadata of type dict, got {type(metadata)}'
        assert service_descriptors is None or isinstance(service_descriptors, list), \
            f'bad type of `service_descriptors` {type(service_descriptors)}'

        # copy metadata so we don't change the original
        metadata_copy = copy.deepcopy(metadata)
        asset_type = metadata_copy['main']['type']
        assert asset_type in ('dataset', 'algorithm'), f'Invalid/unsupported asset type {asset_type}'

        service_descriptors = service_descriptors or []

        services = self._process_service_descriptors(service_descriptors, metadata_copy, publisher_wallet)

        stype_to_service = {s.type: s for s in services}
        checksum_dict = dict()
        for service in services:
            checksum_dict[str(service.index)] = checksum(service.main)

        # Create a DDO object
        asset = Asset()
        # Adding proof to the ddo.
        asset.add_proof(checksum_dict, publisher_wallet)

        # Generating the did and adding to the ddo.
        did = asset.assign_did(DID.did(asset.proof['checksum']))
        logger.debug(f'Generating new did: {did}')
        # Check if it's already registered first!
        if did in self._get_aquarius().list_assets():
            raise OceanDIDAlreadyExist(
                f'Asset id {did} is already registered to another asset.')

        md_service = stype_to_service[ServiceTypes.METADATA]
        ddo_service_endpoint = md_service.service_endpoint
        if '{did}' in ddo_service_endpoint:
            ddo_service_endpoint = ddo_service_endpoint.replace('{did}', did)
            md_service.set_service_endpoint(ddo_service_endpoint)

        # Populate the ddo services
        asset.add_service(md_service)
        access_service = stype_to_service.get(ServiceTypes.ASSET_ACCESS, None)
        compute_service = stype_to_service.get(ServiceTypes.CLOUD_COMPUTE, None)

        if access_service:
            asset.add_service(access_service)
        if compute_service:
            asset.add_service(compute_service)

        asset.proof['signatureValue'] = Web3Helper.sign_hash(
            add_ethereum_prefix_and_hash_msg(asset.asset_id),
            publisher_wallet
        )

        # Add public key and authentication
        asset.add_public_key(did, publisher_wallet.address)

        asset.add_authentication(did, PUBLIC_KEY_TYPE_RSA)

        # Setup metadata service
        # First compute files_encrypted
        assert metadata_copy['main']['files'], \
            'files is required in the metadata main attributes.'
        logger.debug('Encrypting content urls in the metadata.')

        publisher_signature = self._data_provider.sign_message(publisher_wallet, asset.asset_id, self._config)
        encrypt_endpoint = self._data_provider.get_encrypt_endpoint(self._config)
        files_encrypted = self._data_provider.encrypt_files_dict(
            metadata_copy['main']['files'],
            encrypt_endpoint,
            asset.asset_id,
            publisher_wallet.address,
            publisher_signature
        )

        # only assign if the encryption worked
        if files_encrypted:
            logger.debug(f'Content urls encrypted successfully {files_encrypted}')
            index = 0
            for file in metadata_copy['main']['files']:
                file['index'] = index
                index = index + 1
                del file['url']
            metadata_copy['encryptedFiles'] = files_encrypted
        else:
            raise AssertionError('Encrypting the files failed.')

        logger.debug(
            f'Generated asset and services, DID is {asset.did},'
            f' metadata service @{ddo_service_endpoint}.')
        response = None

        if not data_token_address:
            blob = json.dumps({'t': 1, 'url': ddo_service_endpoint})
            name = metadata['main']['name']
            symbol = name
            # register on-chain
            address = DTFactory.configured_address(Web3Helper.get_network_name(), self._config.address_file)
            dtfactory = DTFactory(address)
            tx_id = dtfactory.createToken(
                blob, name, symbol, DataToken.DEFAULT_CAP_BASE, from_wallet=publisher_wallet)
            data_token = DataToken(dtfactory.get_token_address(tx_id))
            if not data_token:
                logger.warning(f'Creating new data token failed.')
                return None

            data_token_address = data_token.address

            logger.info(f'Successfully created data token with address '
                        f'{data_token.address} for new dataset asset with did {did}.')
            # owner_address is set as minter only if creating new data token. So if
            # `data_token_address` is set `owner_address` has no effect.
            if owner_address:
                data_token.setMinter(owner_address, from_wallet=publisher_wallet)

        # Set datatoken address in the asset
        asset.data_token_address = data_token_address

        try:
            # publish the new ddo in ocean-db/Aquarius
            response = self._get_aquarius().publish_asset_ddo(asset)
            logger.info('Asset/ddo published successfully in aquarius.')
        except ValueError as ve:
            raise ValueError(f'Invalid value to publish in the metadata: {str(ve)}')
        except Exception as e:
            logger.error(f'Publish asset in aquarius failed: {str(e)}')
        if not response:
            return None

        return asset

    def retire(self, did: str) -> bool:
        """
        Retire this did of Aquarius

        :param did: DID, str
        :return: bool
        """
        try:
            asset = self.resolve(did)
            metadata_service = asset.get_service(ServiceTypes.METADATA)
            self._get_aquarius(metadata_service.service_endpoint).retire_asset_ddo(did)
            return True
        except AquariusGenericError as err:
            logger.error(err)
            return False

    def resolve(self, did: str) -> Asset:
        """
        When you pass a did retrieve the ddo associated.

        :param did: DID, str
        :return: Asset instance
        """
        return resolve_asset(did, metadata_store_url=self._config.aquarius_url)

    def search(self, text: str, sort=None, offset=100, page=1, aquarius_url=None) -> list:
        """
        Search an asset in oceanDB using aquarius.

        :param text: String with the value that you are searching
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param aquarius_url: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query
        """
        assert page >= 1, f'Invalid page value {page}. Required page >= 1.'
        logger.info(f'Searching asset containing: {text}')
        return [Asset(dictionary=ddo_dict) for ddo_dict in
                self._get_aquarius(aquarius_url).text_search(text, sort, offset, page)['results']]

    def query(self, query: dict, sort=None, offset=100, page=1, aquarius_url=None) -> []:
        """
        Search an asset in oceanDB using search query.

        :param query: dict with query parameters
            (e.g.) https://github.com/oceanprotocol/aquarius/blob/develop/docs/for_api_users/API.md
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param aquarius_url: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query.
        """
        logger.info(f'Searching asset query: {query}')
        aquarius = self._get_aquarius(aquarius_url)
        return [Asset(dictionary=ddo_dict) for ddo_dict in
                aquarius.query_search(query, sort, offset, page)['results']]

    def order(self, did: str, consumer_address: str,
              service_index: [int, None]=None, service_type: str=None) -> OrderRequirements:
        """
        Request a specific service from an asset, returns the service requirements that
        must be met prior to consuming the service.

        :param did:
        :param consumer_address:
        :param service_index:
        :param service_type:
        :return: OrderRequirements instance -- named tuple (amount, data_token_address, receiver_address, nonce),
        """
        assert service_type or service_index, f'One of service_index or service_type is required.'
        asset = self.resolve(did)
        service = ServiceAgreement.from_ddo(ServiceTypes.ASSET_ACCESS, asset)

        dt_address = asset.data_token_address
        sa = ServiceAgreement.from_ddo(service.type, asset)
        initialize_url = self._data_provider.get_initialize_endpoint(sa.service_endpoint)
        order_requirements = self._data_provider.get_order_requirements(
            asset.did, initialize_url, consumer_address, sa.index, sa.type, dt_address
        )
        if not order_requirements:
            raise AssertionError('Data service provider or service is not available.')

        assert dt_address == order_requirements.data_token_address
        return order_requirements

    @staticmethod
    def pay_for_service(amount: int, token_address: str,
                        receiver_address: str, from_wallet: Wallet) -> str:
        """
        Submits the payment for chosen service in DataTokens.

        :param amount:
        :param token_address:
        :param receiver_address:
        :param from_wallet: Wallet instance
        :return: hex str id of transfer transaction
        """
        tokens_amount = int(amount)
        receiver = receiver_address
        dt = DataToken(token_address)
        balance = dt.balanceOf(from_wallet.address)
        if balance < tokens_amount:
            raise AssertionError(f'Your token balance {balance} is not sufficient '
                                 f'to execute the requested service. This service '
                                 f'requires {amount} number of tokens.')

        tx_hash = dt.transfer(receiver, tokens_amount, from_wallet)
        try:
            dt.verify_transfer_tx(tx_hash, from_wallet.address, receiver)
            return tx_hash
        except (AssertionError, Exception) as e:
            msg = (
                f'Downloading asset files failed. The problem is related to '
                f'the transfer of the data tokens required for the download '
                f'service: {e}'
            )
            logger.error(msg)
            raise AssertionError(msg)

    def download(self, did: str, service_index: int, consumer_wallet: Wallet,
                 transfer_tx_id: str, destination: str, index: [int, None]=None) -> str:
        """
        Consume the asset data.

        Using the service endpoint defined in the ddo's service pointed to by service_definition_id.
        Consumer's permissions is checked implicitly by the secret-store during decryption
        of the contentUrls.
        The service endpoint is expected to also verify the consumer's permissions to consume this
        asset.
        This method downloads and saves the asset datafiles to disk.

        :param did: DID, str
        :param service_index: identifier of the service inside the asset DDO, str
        :param consumer_wallet: Wallet instance of the consumer
        :param transfer_tx_id: hex str id of the token transfer transaction
        :param destination: str path
        :param nonce: int value to use in the signature
        :param index: Index of the document that is going to be downloaded, int
        :return: str path to saved files
        """
        asset = self.resolve(did)
        if index is not None:
            assert isinstance(index, int), logger.error('index has to be an integer.')
            assert index >= 0, logger.error('index has to be 0 or a positive integer.')

        service = asset.get_service_by_index(service_index)
        assert service and service.type == ServiceTypes.ASSET_ACCESS, \
            f'Service with index {service_index} and type {ServiceTypes.ASSET_ACCESS} is not found.'

        return download_asset_files(
            service_index,
            asset,
            consumer_wallet,
            destination,
            asset.data_token_address,
            transfer_tx_id,
            self._data_provider,
            index
        )

    def validate(self, metadata: dict) -> bool:
        """
        Validate that the metadata is ok to be stored in aquarius.

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :return: bool
        """
        return self._get_aquarius(self._aquarius_url).validate_metadata(metadata)

    def owner(self, did: str) -> str:
        """
        Return the owner of the asset.

        :param did: DID, str
        :return: the ethereum address of the owner/publisher of given asset did, hex-str
        """
        asset = self.resolve(did)
        return asset.publisher

    def owner_assets(self, owner_address: str) -> list:
        """
        List of Asset objects published by ownerAddress

        :param owner_address: ethereum address of owner/publisher, hex-str
        :return: list of dids
        """
        return [asset.did for asset in self.query({"query": {"proof.creator": [owner_address]}}, offset=1000)]

    @staticmethod
    def _build_access_service(metadata: dict, cost: int, address: str) -> dict:
        return {
            "main": {
                "name": "dataAssetAccessServiceAgreement",
                "creator": address,
                "cost": cost,
                "timeout": 3600,
                "datePublished": metadata[MetadataMain.KEY]['dateCreated']
            }
        }

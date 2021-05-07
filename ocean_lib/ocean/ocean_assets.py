#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import copy
import logging
import lzma
import os
from typing import Optional

from eth_utils import add_0x_prefix, remove_0x_prefix
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.common.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_factory import (
    ServiceDescriptor,
    ServiceFactory,
)
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.aquarius.aquarius import Aquarius
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.common.ddo.public_key_rsa import PUBLIC_KEY_TYPE_RSA
from ocean_lib.common.did import did_to_id
from ocean_lib.common.utils.utilities import checksum
from ocean_lib.data_provider.data_service_provider import (
    DataServiceProvider,
    OrderRequirements,
)
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.exceptions import (
    AquariusError,
    ContractNotFound,
    InsufficientBalance,
    VerifyTxFailed,
)
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.metadata import MetadataContract
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.utils import (
    add_ethereum_prefix_and_hash_msg,
    get_network_name,
)
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from plecos import plecos

logger = logging.getLogger("ocean")


@enforce_types_shim
class OceanAssets:

    """Ocean assets class."""

    def __init__(self, config, data_provider, ddo_registry_address):
        """Initialises OceanAssets object."""
        self._config = config
        self._metadata_cache_uri = config.metadata_cache_uri
        self._data_provider = data_provider
        self._metadata_registry_address = ddo_registry_address

        downloads_path = os.path.join(os.getcwd(), "downloads")
        if self._config.has_option("resources", "downloads.path"):
            downloads_path = (
                self._config.get("resources", "downloads.path") or downloads_path
            )
        self._downloads_path = downloads_path

    def ddo_registry(self):
        return MetadataContract(self._metadata_registry_address)

    def _get_aquarius(self, url=None) -> Aquarius:
        return AquariusProvider.get_aquarius(url or self._metadata_cache_uri)

    def _process_service_descriptors(
        self,
        service_descriptors: list,
        metadata: dict,
        provider_uri: str,
        wallet: Wallet,
    ) -> list:
        ddo_service_endpoint = self._get_aquarius().get_service_endpoint()

        service_type_to_descriptor = {sd[0]: sd for sd in service_descriptors}
        _service_descriptors = []
        metadata_service_desc = service_type_to_descriptor.pop(
            ServiceTypes.METADATA,
            ServiceDescriptor.metadata_service_descriptor(
                metadata, ddo_service_endpoint
            ),
        )
        _service_descriptors = [metadata_service_desc]

        # Always dafault to creating a ServiceTypes.ASSET_ACCESS service if no services are specified
        access_service_descriptor = service_type_to_descriptor.pop(
            ServiceTypes.ASSET_ACCESS, None
        )
        compute_service_descriptor = service_type_to_descriptor.pop(
            ServiceTypes.CLOUD_COMPUTE, None
        )
        # Make an access service only if no services are given by the user.
        if not access_service_descriptor and not compute_service_descriptor:
            access_service_descriptor = ServiceDescriptor.access_service_descriptor(
                self.build_access_service(
                    metadata["main"]["dateCreated"], 1.0, wallet.address
                ),
                self._data_provider.build_download_endpoint(provider_uri)[1],
            )

        if access_service_descriptor:
            _service_descriptors.append(access_service_descriptor)
        if compute_service_descriptor:
            _service_descriptors.append(compute_service_descriptor)

        _service_descriptors.extend(service_type_to_descriptor.values())
        return ServiceFactory.build_services(_service_descriptors)

    def create(
        self,
        metadata: dict,
        publisher_wallet: Wallet,
        service_descriptors: list = None,
        owner_address: str = None,
        data_token_address: str = None,
        provider_uri=None,
        dt_name: str = None,
        dt_symbol: str = None,
        dt_blob: str = None,
        dt_cap: float = None,
    ) -> (Asset, None):
        """Register an asset on-chain.

        Creating/deploying a DataToken contract and in the Metadata store (Aquarius).

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :param publisher_wallet: Wallet of the publisher registering this asset
        :param service_descriptors: list of ServiceDescriptor tuples of length 2.
            The first item must be one of ServiceTypes and the second
            item is a dict of parameters and values required by the service
        :param owner_address: hex str the ethereum address to assign asset ownership to. After
            registering the asset on-chain, the ownership is transferred to this address
        :param data_token_address: hex str the address of the data token smart contract. The new
            asset will be associated with this data token address.
        :param provider_uri: str URL of service provider. This will be used as base to
            construct the serviceEndpoint for the `access` (download) service
        :param dt_name: str name of DataToken if creating a new one
        :param dt_symbol: str symbol of DataToken if creating a new one
        :param dt_blob: str blob of DataToken if creating a new one. A `blob` is any text
            to be stored with the ERC20 DataToken contract for any purpose.
        :param dt_cap: float
        :return: DDO instance
        """
        assert isinstance(
            metadata, dict
        ), f"Expected metadata of type dict, got {type(metadata)}"
        assert service_descriptors is None or isinstance(
            service_descriptors, list
        ), f"bad type of `service_descriptors` {type(service_descriptors)}"

        # copy metadata so we don't change the original
        metadata_copy = copy.deepcopy(metadata)
        asset_type = metadata_copy["main"]["type"]
        assert asset_type in (
            "dataset",
            "algorithm",
        ), f"Invalid/unsupported asset type {asset_type}"
        if not plecos.is_valid_dict_local(metadata_copy):
            errors = plecos.list_errors_dict_local(metadata_copy)
            msg = f"Metadata has validation errors: {errors}"
            logger.error(msg)
            raise ValueError(msg)

        urls = [item["url"] for item in metadata["main"]["files"]]
        for url in urls:
            if not DataServiceProvider.check_single_file_info(url, provider_uri):
                msg = f"The URL of this service can not be accessed: {url}."
                logger.error(msg)
                raise ValueError(msg)

        service_descriptors = service_descriptors or []

        services = self._process_service_descriptors(
            service_descriptors, metadata_copy, provider_uri, publisher_wallet
        )

        stype_to_service = {s.type: s for s in services}
        checksum_dict = dict()
        for service in services:
            checksum_dict[str(service.index)] = checksum(service.main)

        # Create a DDO object
        asset = Asset()
        # Adding proof to the ddo.
        asset.add_proof(checksum_dict, publisher_wallet)

        #################
        # DataToken
        address = DTFactory.configured_address(
            get_network_name(), self._config.address_file
        )
        dtfactory = DTFactory(address)
        if not data_token_address:
            blob = dt_blob or ""
            name = dt_name or metadata["main"]["name"]
            symbol = dt_symbol or name
            # register on-chain
            _cap = dt_cap if dt_cap else DataToken.DEFAULT_CAP
            tx_id = dtfactory.createToken(
                blob, name, symbol, to_base_18(_cap), from_wallet=publisher_wallet
            )
            data_token = DataToken(dtfactory.get_token_address(tx_id))
            if not data_token:
                logger.warning("Creating new data token failed.")
                return None

            data_token_address = data_token.address

            logger.info(
                f"Successfully created data token with address "
                f"{data_token.address} for new dataset asset."
            )
            # owner_address is set as minter only if creating new data token. So if
            # `data_token_address` is set `owner_address` has no effect.
            if owner_address:
                data_token.proposeMinter(owner_address, from_wallet=publisher_wallet)
        else:
            # verify data_token_address
            dt = DataToken(data_token_address)
            minter = dt.contract_concise.minter()
            if not minter:
                raise AssertionError(
                    f"datatoken address {data_token_address} does not seem to be a valid DataToken contract."
                )
            elif minter.lower() != publisher_wallet.address.lower():
                raise AssertionError(
                    f"Minter of datatoken {data_token_address} is not the same as the publisher."
                )
            elif not dtfactory.verify_data_token(data_token_address):
                raise ContractNotFound(
                    f"datatoken address {data_token_address} is not found in the DTFactory events."
                )

        assert (
            data_token_address
        ), "data_token_address is required for publishing a dataset asset."

        # Generating the did and adding to the ddo.
        did = asset.assign_did(f"did:op:{remove_0x_prefix(data_token_address)}")
        logger.debug(f"Using datatoken address as did: {did}")
        # Check if it's already registered first!
        if did in self._get_aquarius().list_assets():
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )

        md_service = stype_to_service[ServiceTypes.METADATA]
        ddo_service_endpoint = md_service.service_endpoint
        if "{did}" in ddo_service_endpoint:
            ddo_service_endpoint = ddo_service_endpoint.replace("{did}", did)
            md_service.set_service_endpoint(ddo_service_endpoint)

        # Populate the ddo services
        asset.add_service(md_service)
        access_service = stype_to_service.get(ServiceTypes.ASSET_ACCESS, None)
        compute_service = stype_to_service.get(ServiceTypes.CLOUD_COMPUTE, None)

        if access_service:
            asset.add_service(access_service)
        if compute_service:
            asset.add_service(compute_service)

        asset.proof["signatureValue"] = sign_hash(
            add_ethereum_prefix_and_hash_msg(asset.asset_id), publisher_wallet
        )

        # Add public key and authentication
        asset.add_public_key(did, publisher_wallet.address)

        asset.add_authentication(did, PUBLIC_KEY_TYPE_RSA)

        # Setup metadata service
        # First compute files_encrypted
        assert metadata_copy["main"][
            "files"
        ], "files is required in the metadata main attributes."
        logger.debug("Encrypting content urls in the metadata.")

        publisher_signature = self._data_provider.sign_message(
            publisher_wallet, asset.asset_id, provider_uri=provider_uri
        )
        _, encrypt_endpoint = self._data_provider.build_encrypt_endpoint(provider_uri)
        files_encrypted = self._data_provider.encrypt_files_dict(
            metadata_copy["main"]["files"],
            encrypt_endpoint,
            asset.asset_id,
            publisher_wallet.address,
            publisher_signature,
        )

        # only assign if the encryption worked
        if files_encrypted:
            logger.debug(f"Content urls encrypted successfully {files_encrypted}")
            index = 0
            for file in metadata_copy["main"]["files"]:
                file["index"] = index
                index = index + 1
                del file["url"]
            metadata_copy["encryptedFiles"] = files_encrypted
        else:
            raise AssertionError("Encrypting the files failed.")

        logger.debug(
            f"Generated asset and services, DID is {asset.did},"
            f" metadata service @{ddo_service_endpoint}."
        )

        # Set datatoken address in the asset
        asset.data_token_address = data_token_address

        try:
            # publish the new ddo in ocean-db/Aquarius
            ddo_registry = self.ddo_registry()
            web3 = Web3Provider.get_web3()
            tx_id = ddo_registry.create(
                asset.asset_id,
                bytes([1]),
                lzma.compress(web3.toBytes(text=asset.as_text())),
                publisher_wallet,
            )
            if not ddo_registry.verify_tx(tx_id):
                raise VerifyTxFailed(
                    f"create DDO on-chain failed, transaction status is 0. Transaction hash is {tx_id}"
                )
            logger.info("Asset/ddo published on-chain successfully.")
        except ValueError as ve:
            raise ValueError(f"Invalid value to publish in the metadata: {str(ve)}")
        except Exception as e:
            logger.error(f"Publish asset on-chain failed: {str(e)}")
            raise

        return asset

    def update(self, asset: Asset, publisher_wallet: Wallet) -> str:
        try:
            # publish the new ddo in ocean-db/Aquarius
            ddo_registry = self.ddo_registry()
            web3 = Web3Provider.get_web3()
            tx_id = ddo_registry.update(
                asset.asset_id,
                bytes([1]),
                lzma.compress(web3.toBytes(text=asset.as_text())),
                publisher_wallet,
            )
            if not ddo_registry.verify_tx(tx_id):
                raise VerifyTxFailed(
                    f"update DDO on-chain failed, transaction status is 0. Transaction hash is {tx_id}"
                )
            logger.info("Asset/ddo updated on-chain successfully.")
            return tx_id
        except ValueError as ve:
            raise ValueError(f"Invalid value to publish in the metadata: {str(ve)}")
        except Exception as e:
            logger.error(f"Publish asset on-chain failed: {str(e)}")
            raise

    def resolve(self, did: str) -> Asset:
        """
        When you pass a did retrieve the ddo associated.

        :param did: DID, str
        :return: Asset instance
        """
        return resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)

    def search(
        self, text: str, sort=None, offset=100, page=1, metadata_cache_uri=None
    ) -> list:
        """
        Search an asset in oceanDB using aquarius.

        :param text: String with the value that you are searching
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param metadata_cache_uri: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query
        """
        assert page >= 1, f"Invalid page value {page}. Required page >= 1."
        logger.info(f"Searching asset containing: {text}")
        return [
            Asset(dictionary=ddo_dict)
            for ddo_dict in self._get_aquarius(metadata_cache_uri).query_search(
                {"query": {"query_string": {"query": text}}}, sort, offset, page
            )["results"]
        ]

    def query(
        self, query: dict, sort=None, offset=100, page=1, metadata_cache_uri=None
    ) -> []:
        """
        Search an asset in oceanDB using search query.

        :param query: dict with query parameters
            (e.g.) https://github.com/oceanprotocol/aquarius/blob/develop/docs/for_api_users/API.md
        :param sort: Dictionary to choose order main in some value
        :param offset: Number of elements shows by page
        :param page: Page number
        :param metadata_cache_uri: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query.
        """
        logger.info(f"Searching asset query: {query}")
        aquarius = self._get_aquarius(metadata_cache_uri)
        return [
            Asset(dictionary=ddo_dict)
            for ddo_dict in aquarius.query_search({"query": query}, sort, offset, page)[
                "results"
            ]
        ]

    def order(
        self,
        did: str,
        consumer_address: str,
        service_index: Optional[int] = None,
        service_type: str = None,
    ) -> OrderRequirements:
        """
        Request a specific service from an asset, returns the service requirements that
        must be met prior to consuming the service.

        :param did:
        :param consumer_address:
        :param service_index:
        :param service_type:
        :return: OrderRequirements instance -- named tuple (amount, data_token_address, receiver_address, nonce),
        """
        assert (
            service_type or service_index
        ), "One of service_index or service_type is required."
        asset = self.resolve(did)

        if service_type:
            sa = ServiceAgreement.from_ddo(service_type, asset)
        else:
            service = asset.get_service_by_index(service_index)
            sa = ServiceAgreement.from_ddo(service.type, asset)

        consumable_result = asset.is_consumable(
            {"type": "address", "value": consumer_address},
            provider_uri=sa.service_endpoint,
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        dt_address = asset.data_token_address

        _, initialize_url = self._data_provider.build_initialize_endpoint(
            sa.service_endpoint
        )
        order_requirements = self._data_provider.get_order_requirements(
            asset.did, initialize_url, consumer_address, sa.index, sa.type, dt_address
        )
        if not order_requirements:
            raise AssertionError("Data service provider or service is not available.")

        assert (
            dt_address == order_requirements.data_token_address
        ), "Asset's datatoken address does not match the requirements. "
        return order_requirements

    @staticmethod
    def pay_for_service(
        amount: float,
        token_address: str,
        did: str,
        service_id: int,
        fee_receiver: str,
        from_wallet: Wallet,
        consumer: str = None,
    ) -> str:
        """
        Submits the payment for chosen service in DataTokens.

        :param amount:
        :param token_address:
        :param did:
        :param service_id:
        :param fee_receiver:
        :param from_wallet: Wallet instance
        :param consumer: str the address of consumer of the service, defaults to the payer (the `from_wallet` address)
        :return: hex str id of transfer transaction
        """
        amount_base = to_base_18(amount)
        dt = DataToken(token_address)
        balance = dt.balanceOf(from_wallet.address)
        if balance < amount_base:
            raise InsufficientBalance(
                f"Your token balance {balance} is not sufficient "
                f"to execute the requested service. This service "
                f"requires {amount_base} number of tokens."
            )

        if did.startswith("did:"):
            did = add_0x_prefix(did_to_id(did))

        if fee_receiver is None:
            fee_receiver = ZERO_ADDRESS

        if consumer is None:
            consumer = from_wallet.address

        tx_hash = dt.startOrder(
            consumer, amount_base, service_id, fee_receiver, from_wallet
        )

        try:
            dt.verify_order_tx(
                Web3Provider.get_web3(),
                tx_hash,
                did,
                service_id,
                amount_base,
                from_wallet.address,
            )
            return tx_hash
        except (AssertionError, Exception) as e:
            msg = (
                f"Downloading asset files failed. The problem is related to "
                f"the transfer of the data tokens required for the download "
                f"service: {e}"
            )
            logger.error(msg)
            raise AssertionError(msg)

    def download(
        self,
        did: str,
        service_index: int,
        consumer_wallet: Wallet,
        order_tx_id: str,
        destination: str,
        index: Optional[int] = None,
    ) -> str:
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
        :param order_tx_id: hex str id of the token transfer transaction
        :param destination: str path
        :param index: Index of the document that is going to be downloaded, int
        :return: str path to saved files
        """
        asset = self.resolve(did)
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")

        service = asset.get_service_by_index(service_index)
        assert (
            service and service.type == ServiceTypes.ASSET_ACCESS
        ), f"Service with index {service_index} and type {ServiceTypes.ASSET_ACCESS} is not found."

        consumable_result = asset.is_consumable(
            {"type": "address", "value": consumer_wallet.address},
            provider_uri=service.service_endpoint,
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        return download_asset_files(
            service_index,
            asset,
            consumer_wallet,
            destination,
            asset.data_token_address,
            order_tx_id,
            self._data_provider,
            index,
        )

    def validate(self, metadata: dict) -> bool:
        """
        Validate that the metadata is ok to be stored in aquarius.

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :return: bool
        """
        return self._get_aquarius(self._metadata_cache_uri).validate_metadata(metadata)

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
        return [
            asset.did
            for asset in self.query(
                {"query_string": {"query": owner_address, "fields": ["proof.creator"]}},
                offset=1000,
            )
        ]

    @staticmethod
    def build_access_service(
        date_created: str, cost: float, address: str, timeout=3600
    ) -> dict:
        return {
            "main": {
                "name": "dataAssetAccessServiceAgreement",
                "creator": address,
                "cost": cost,
                "timeout": timeout,
                "datePublished": date_created,
            }
        }

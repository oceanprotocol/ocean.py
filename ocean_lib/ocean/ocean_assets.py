#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import copy
import logging
import lzma
import os
from pathlib import Path
from typing import Optional, Tuple, Type, Union

from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from eth_utils import add_0x_prefix, remove_0x_prefix
from web3.main import Web3

from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.assets.did import did_to_id
from ocean_lib.common.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.aquarius.aquarius import Aquarius
from ocean_lib.common.aquarius.aquarius_provider import AquariusProvider
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import (
    DataServiceProvider,
    OrderRequirements,
)
from ocean_lib.exceptions import (
    AquariusError,
    ContractNotFound,
    InsufficientBalance,
    VerifyTxFailed,
)
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.metadata import MetadataContract
from ocean_lib.services.service import Service
from ocean_lib.utils.utilities import checksum
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import pretty_ether_and_wei
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.utils import get_network_name
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger("ocean")


class OceanAssets:

    """Ocean assets class."""

    @enforce_types
    def __init__(
        self,
        config: Config,
        web3: Web3,
        data_provider: Type[DataServiceProvider],
        ddo_registry_address: str,
    ) -> None:
        """Initialises OceanAssets object."""
        self._config = config
        self._web3 = web3
        self._metadata_cache_uri = config.metadata_cache_uri
        self._data_provider = data_provider
        self._metadata_registry_address = ddo_registry_address

        downloads_path = os.path.join(os.getcwd(), "downloads")
        if self._config.has_option("resources", "downloads.path"):
            downloads_path = (
                self._config.get("resources", "downloads.path") or downloads_path
            )
        self._downloads_path = downloads_path

    @enforce_types
    def ddo_registry(self) -> MetadataContract:
        return MetadataContract(self._web3, self._metadata_registry_address)

    @enforce_types
    def _get_aquarius(self, url: Optional[str] = None) -> Aquarius:
        return AquariusProvider.get_aquarius(url or self._metadata_cache_uri)

    @enforce_types
    def _build_asset_contents(self, asset: V3Asset, encrypt: bool = False):
        if not encrypt:
            return bytes([1]), lzma.compress(Web3.toBytes(text=asset.as_text()))

        return bytes([2]), self._get_aquarius().encrypt(asset.as_text())

    @enforce_types
    def create(
        self,
        metadata: dict,
        publisher_wallet: Wallet,
        services: Optional[list] = None,
        owner_address: Optional[str] = None,
        data_token_address: Optional[str] = None,
        provider_uri: Optional[str] = None,
        dt_name: Optional[str] = None,
        dt_symbol: Optional[str] = None,
        dt_blob: Optional[str] = None,
        dt_cap: Optional[int] = None,
        encrypt: Optional[bool] = False,
    ) -> Optional[V3Asset]:
        """Register an asset on-chain.

        Creating/deploying a DataToken contract and in the Metadata store (Aquarius).

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :param publisher_wallet: Wallet of the publisher registering this asset
        :param services: list of Service objects.
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
        :param dt_cap: int amount of DataTokens to mint, denoted in wei
        :return: DDO instance
        """
        assert isinstance(
            metadata, dict
        ), f"Expected metadata of type dict, got {type(metadata)}"

        # copy metadata so we don't change the original
        metadata_copy = copy.deepcopy(metadata)
        asset_type = metadata_copy["main"]["type"]
        assert asset_type in (
            "dataset",
            "algorithm",
        ), f"Invalid/unsupported asset type {asset_type}"

        validation_result, validation_errors = self.validate(metadata)
        if not validation_result:
            msg = f"Metadata has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        urls = [item["url"] for item in metadata["main"]["files"]]
        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config)
        for url in urls:
            if not DataServiceProvider.check_single_file_info(url, provider_uri):
                msg = f"The URL of this service can not be accessed: {url}."
                logger.error(msg)
                raise ValueError(msg)

        services = services or []
        services = self._add_defaults(
            services, metadata_copy, provider_uri, publisher_wallet
        )

        checksum_dict = dict()
        for service in services:
            checksum_dict[str(service.index)] = checksum(service.main)

        # Create a DDO object
        asset = V3Asset()
        # Adding proof to the ddo.
        asset.add_proof(checksum_dict, publisher_wallet)

        #################
        # DataToken
        address = DTFactory.configured_address(
            get_network_name(web3=self._web3), self._config.address_file
        )
        dtfactory = DTFactory(self._web3, address)
        if not data_token_address:
            blob = dt_blob or ""
            name = dt_name or metadata["main"]["name"]
            symbol = dt_symbol or name
            # register on-chain
            _cap = dt_cap if dt_cap else DataToken.DEFAULT_CAP
            tx_id = dtfactory.createToken(
                blob, name, symbol, _cap, from_wallet=publisher_wallet
            )
            data_token = DataToken(self._web3, dtfactory.get_token_address(tx_id))
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
            if not dtfactory.verify_data_token(data_token_address):
                raise ContractNotFound(
                    f"datatoken address {data_token_address} is not found in the DTFactory events."
                )
            # verify data_token_address
            dt = DataToken(self._web3, data_token_address)
            minter = dt.contract.caller.minter()
            if not minter:
                raise AssertionError(
                    f"datatoken address {data_token_address} does not seem to be a valid DataToken contract."
                )
            elif minter.lower() != publisher_wallet.address.lower():
                raise AssertionError(
                    f"Minter of datatoken {data_token_address} is not the same as the publisher."
                )

        assert (
            data_token_address
        ), "data_token_address is required for publishing a dataset asset."

        # Generating the did and adding to the ddo.
        did = f"did:op:{remove_0x_prefix(data_token_address)}"
        asset.did = did
        logger.debug(f"Using datatoken address as did: {did}")
        # Check if it's already registered first!
        if self._get_aquarius().ddo_exists(did):
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )

        for service in services:
            if service.type == ServiceTypes.METADATA:
                ddo_service_endpoint = service.service_endpoint
                if "{did}" in ddo_service_endpoint:
                    ddo_service_endpoint = ddo_service_endpoint.replace("{did}", did)
                    service.service_endpoint = ddo_service_endpoint

            asset.add_service(service)

        asset.proof["signatureValue"] = sign_hash(
            encode_defunct(text=asset.asset_id), publisher_wallet
        )

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
        flags, asset_contents = self._build_asset_contents(asset, encrypt)

        try:
            # publish the new ddo in ocean-db/Aquarius
            ddo_registry = self.ddo_registry()
            tx_id = ddo_registry.create(
                asset.asset_id, flags, asset_contents, publisher_wallet
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

    @enforce_types
    def _add_defaults(
        self, services: list, metadata: dict, provider_uri: str, wallet: Wallet
    ) -> list:
        ddo_service_endpoint = self._get_aquarius().get_service_endpoint()

        metadata_service = Service(
            service_endpoint=ddo_service_endpoint,
            service_type=ServiceTypes.METADATA,
            attributes=metadata,
        )

        services.append(metadata_service)

        has_access_service = False
        for service in services:
            if service.type == ServiceTypes.ASSET_ACCESS:
                has_access_service = True

        if not has_access_service:
            access_service = self.build_access_service(
                self._data_provider.build_download_endpoint(provider_uri)[1],
                metadata["main"]["dateCreated"],
                1.0,
                wallet.address,
            )

            services.append(access_service)

        return services

    @enforce_types
    def update(
        self, asset: V3Asset, publisher_wallet: Wallet, encrypt: Optional[bool] = False
    ) -> str:
        try:
            # publish the new ddo in ocean-db/Aquarius
            ddo_registry = self.ddo_registry()

            flags, asset_contents = self._build_asset_contents(asset, encrypt)
            tx_id = ddo_registry.update(
                asset.asset_id, flags, asset_contents, publisher_wallet
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

    @enforce_types
    def resolve(self, did: str) -> V3Asset:
        """
        When you pass a did retrieve the ddo associated.

        :param did: DID, str
        :return: Asset instance
        """
        return resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)

    @enforce_types
    def search(self, text: str, metadata_cache_uri: Optional[str] = None) -> list:
        """
        Search an asset in oceanDB using aquarius.

        :param text: String with the value that you are searching
        :param metadata_cache_uri: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query
        """
        logger.info(f"Searching asset containing: {text}")
        return [
            V3Asset(dictionary=ddo_dict)
            for ddo_dict in self._get_aquarius(metadata_cache_uri).query_search(
                {"query": {"query_string": {"query": text}}}
            )
        ]

    @enforce_types
    def query(self, query: dict, metadata_cache_uri: Optional[str] = None) -> list:
        """
        Search an asset in oceanDB using search query.

        :param query: dict with query parameters
            (e.g.) https://github.com/oceanprotocol/aquarius/blob/develop/docs/for_api_users/API.md
        :param metadata_cache_uri: Url of the aquarius where you want to search. If there is not
            provided take the default
        :return: List of assets that match with the query.
        """
        logger.info(f"Searching asset query: {query}")
        aquarius = self._get_aquarius(metadata_cache_uri)
        return [
            V3Asset(dictionary=ddo_dict) for ddo_dict in aquarius.query_search(query)
        ]

    @enforce_types
    def order(
        self,
        did: str,
        consumer_address: str,
        service_index: Optional[int] = None,
        service_type: Optional[str] = None,
        userdata: Optional[dict] = None,
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
            sa = asset.get_service(service_type)
        else:
            service = asset.get_service_by_index(service_index)
            sa = asset.get_service(service.type)

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
            asset.did,
            initialize_url,
            consumer_address,
            sa.index,
            sa.type,
            dt_address,
            userdata,
        )
        if not order_requirements:
            raise AssertionError("Data service provider or service is not available.")

        assert (
            dt_address == order_requirements.data_token_address
        ), "Asset's datatoken address does not match the requirements. "
        return order_requirements

    @staticmethod
    @enforce_types
    def pay_for_service(
        web3: Web3,
        amount: int,
        token_address: str,
        did: str,
        service_id: int,
        fee_receiver: str,
        from_wallet: Wallet,
        consumer: str,
    ) -> str:
        """
        Submits the payment for chosen service in DataTokens.

        :param amount:
        :param token_address:
        :param did:
        :param service_id:
        :param fee_receiver:
        :param from_wallet: Wallet instance
        :param consumer: str the address of consumer of the service
        :return: hex str id of transfer transaction
        """
        dt = DataToken(web3, token_address)
        balance = dt.balanceOf(from_wallet.address)
        if balance < amount:
            raise InsufficientBalance(
                f"Your token balance {pretty_ether_and_wei(balance, dt.symbol())} is not sufficient "
                f"to execute the requested service. This service "
                f"requires {pretty_ether_and_wei(amount, dt.symbol())}."
            )

        if did.startswith("did:"):
            did = add_0x_prefix(did_to_id(did))

        if fee_receiver is None:
            fee_receiver = ZERO_ADDRESS

        tx_hash = dt.startOrder(consumer, amount, service_id, fee_receiver, from_wallet)

        try:
            dt.verify_order_tx(tx_hash, did, service_id, amount, from_wallet.address)
            return tx_hash
        except (AssertionError, Exception) as e:
            msg = (
                f"Downloading asset files failed. The problem is related to "
                f"the transfer of the data tokens required for the download "
                f"service: {e}"
            )
            logger.error(msg)
            raise AssertionError(msg)

    @enforce_types
    def download(
        self,
        did: str,
        service_index: int,
        consumer_wallet: Wallet,
        order_tx_id: str,
        destination: Union[str, Path],
        index: Optional[int] = None,
        userdata: Optional[dict] = None,
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
            userdata,
        )

    @enforce_types
    def validate(self, metadata: dict) -> Tuple[bool, list]:
        """
        Validate that the metadata is ok to be stored in aquarius.

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :return: (bool, list) list of errors, empty if valid
        """
        return self._get_aquarius(self._metadata_cache_uri).validate_metadata(metadata)

    @enforce_types
    def owner(self, did: str) -> str:
        """
        Return the owner of the asset.

        :param did: DID, str
        :return: the ethereum address of the owner/publisher of given asset did, hex-str
        """
        asset = self.resolve(did)
        return asset.publisher

    @enforce_types
    def owner_assets(self, owner_address: str) -> list:
        """
        List of Asset objects published by ownerAddress

        :param owner_address: ethereum address of owner/publisher, hex-str
        :return: list of dids
        """
        return [
            asset.did
            for asset in self.query(
                {
                    "size": 1000,
                    "query": {
                        "query_string": {
                            "query": owner_address,
                            "fields": ["proof.creator"],
                        }
                    },
                }
            )
        ]

    @staticmethod
    @enforce_types
    def build_access_service(
        endpoint: str,
        date_created: str,
        cost: float,
        address: str,
        timeout: Optional[int] = 3600,
    ) -> dict:
        attributes = {
            "main": {
                "name": "dataAssetAccessServiceAgreement",
                "creator": address,
                "cost": cost,
                "timeout": timeout,
                "datePublished": date_created,
            }
        }

        return Service(
            service_endpoint=endpoint,
            service_type=ServiceTypes.ASSET_ACCESS,
            attributes=attributes,
        )

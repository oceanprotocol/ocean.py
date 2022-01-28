#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import json
import logging
import lzma
import os
from typing import List, Optional, Tuple, Type

from enforce_typing import enforce_types
from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.aquarius import Aquarius
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_downloader import download_asset_files
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import AquariusError, ContractNotFound, InsufficientBalance
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_token import ERC721Token
from ocean_lib.models.models_structures import ChainMetadata, CreateErc20Data
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.services.service import Service
from ocean_lib.utils.utilities import create_checksum
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import pretty_ether_and_wei, to_wei
from ocean_lib.web3_internal.wallet import Wallet
from web3 import Web3

logger = logging.getLogger("ocean")


@enforce_types
class OceanAssets:
    """Ocean asset class for V4."""

    def __init__(
        self, config: Config, web3: Web3, data_provider: Type[DataServiceProvider]
    ) -> None:
        """Initialises OceanAssets object."""
        self._config = config
        self._web3 = web3
        self._metadata_cache_uri = config.metadata_cache_uri
        self._data_provider = data_provider

        downloads_path = os.path.join(os.getcwd(), "downloads")
        if self._config.has_option("resources", "downloads.path"):
            downloads_path = (
                self._config.get("resources", "downloads.path") or downloads_path
            )
        self._downloads_path = downloads_path
        self._aquarius = Aquarius.get_instance(self._metadata_cache_uri)

    def validate(self, asset: Asset) -> Tuple[bool, list]:
        """
        Validate that the asset is ok to be stored in aquarius.

        :param asset: Asset.
        :return: (bool, list) list of errors, empty if valid
        """
        return self._aquarius.validate_asset(asset)

    def _add_defaults(
        self, services: list, datatoken: str, files: str, provider_uri: str
    ) -> list:
        has_access_service = any(
            map(
                lambda s: s.type == ServiceTypes.ASSET_ACCESS
                and s.id == self.find_service_by_datatoken(datatoken, services),
                services,
            )
        )

        if not has_access_service:
            access_service = self.build_access_service(
                service_id="0",
                service_endpoint=self._data_provider.build_download_endpoint(
                    provider_uri
                )[1],
                datatoken=datatoken,
                files=files,
            )

            services.append(access_service)

        return services

    @staticmethod
    def build_access_service(
        service_id: str,
        service_endpoint: str,
        datatoken: str,
        files: str,
        timeout: Optional[int] = 3600,
    ) -> Service:

        return Service(
            service_id=service_id,
            service_type=ServiceTypes.ASSET_ACCESS,
            service_endpoint=service_endpoint,
            datatoken=datatoken,
            files=files,
            timeout=timeout,
        )

    def deploy_datatoken(
        self,
        erc721_factory: ERC721FactoryContract,
        erc721_token: ERC721Token,
        erc20_data: CreateErc20Data,
        from_wallet: Wallet,
    ) -> str:
        tx_result = erc721_token.create_erc20(erc20_data, from_wallet)
        assert tx_result, "Failed to create ERC20 token."

        tx_receipt = self._web3.eth.wait_for_transaction_receipt(tx_result)
        registered_token_event = erc721_factory.get_event_log(
            ERC721FactoryContract.EVENT_TOKEN_CREATED,
            tx_receipt.blockNumber,
            self._web3.eth.block_number,
            None,
        )
        assert registered_token_event, "Cannot find TokenCreated event."

        return registered_token_event[0].args.newTokenAddress

    def find_service_by_datatoken(self, datatoken: str, services: list) -> str:
        return next(
            (service.id for service in services if service.datatoken == datatoken), None
        )

    def build_datatokens_list(
        self, services: list, deployed_erc20_tokens: list
    ) -> list:
        datatokens = []
        # (1-n) service per datatoken, 1 datatoken per service
        for erc20_token in deployed_erc20_tokens:
            datatokens = datatokens + [
                {
                    "address": erc20_token.address,
                    "name": erc20_token.contract.caller.name(),
                    "symbol": erc20_token.symbol(),
                    "serviceId": service.id,
                }
                for service in services
                if service.datatoken == erc20_token.address
            ]

        return datatokens

    @staticmethod
    def _encrypt_ddo(
        asset: Asset,
        provider_uri: str,
        encrypt_flag: Optional[bool] = False,
        compress_flag: Optional[bool] = False,
    ):
        # Process the DDO
        asset_dict = asset.as_dictionary()
        ddo_string = json.dumps(asset_dict, separators=(",", ":"))
        ddo_bytes = ddo_string.encode("utf-8")
        ddo_hash = create_checksum(ddo_string)

        # Plain asset
        if not encrypt_flag and not compress_flag:
            flags = bytes([0])
            document = ddo_bytes
            return document, flags, ddo_hash

        # Only compression, not encrypted
        if compress_flag and not encrypt_flag:
            flags = bytes([1])
            # Compress DDO
            document = lzma.compress(ddo_bytes)
            return document, flags, ddo_hash

        # Only encryption, not compressed
        if encrypt_flag and not compress_flag:
            flags = bytes([2])
            # Encrypt DDO
            encrypt_response = DataServiceProvider.encrypt(
                objects_to_encrypt=ddo_string,
                encrypt_endpoint=f"{provider_uri}/api/services/encrypt",
            )
            document = encrypt_response.text
            return document, flags, ddo_hash

        # Encrypted & compressed
        flags = bytes([3])
        # Compress DDO
        compressed_document = lzma.compress(ddo_bytes)

        # Encrypt DDO
        encrypt_response = DataServiceProvider.encrypt(
            objects_to_encrypt=compressed_document,
            encrypt_endpoint=f"{provider_uri}/api/services/encrypt",
        )

        document = encrypt_response.text

        return document, flags, ddo_hash

    @staticmethod
    def _assert_ddo_metadata(metadata: dict):
        assert isinstance(
            metadata, dict
        ), f"Expected metadata of type dict, got {type(metadata)}"

        asset_type = metadata.get("type")

        assert asset_type in (
            "dataset",
            "algorithm",
        ), f"Invalid/unsupported asset type {asset_type}"

        assert "name" in metadata, "Must have name in metadata."

    def create(
        self,
        metadata: dict,
        publisher_wallet: Wallet,
        encrypted_files: Optional[str] = None,
        services: Optional[list] = None,
        credentials: Optional[dict] = None,
        provider_uri: Optional[str] = None,
        erc721_address: Optional[str] = None,
        erc721_name: Optional[str] = None,
        erc721_symbol: Optional[str] = None,
        template_index: Optional[int] = 1,
        erc721_additional_erc_deployer: Optional[str] = None,
        erc721_uri: Optional[str] = None,
        erc20_tokens_data: Optional[List[CreateErc20Data]] = None,
        deployed_erc20_tokens: Optional[List[ERC20Token]] = None,
        encrypt_flag: Optional[bool] = False,
        compress_flag: Optional[bool] = False,
    ) -> Optional[Asset]:
        """Register an asset on-chain.

        Creating/deploying a ERC721Token contract and in the Metadata store (Aquarius).

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :param publisher_wallet: Wallet of the publisher registering this asset.
        :param encrypted_files: str of the files that need to be encrypted before publishing.
        :param services: list of Service objects.
        :param credentials: credentials dict necessary for the asset.
        :param provider_uri: str URL of service provider. This will be used as base to
        construct the serviceEndpoint for the `access` (download) service
        :param erc721_address: hex str the address of the ERC721 token. The new
        asset will be associated with this ERC721 token address.
        :param erc721_name: str name of ERC721 token if creating a new one
        :param erc721_symbol: str symbol of ERC721 token  if creating a new one
        :param template_index: int template index of the ERC721 token, by default is 1.
        :param erc721_additional_erc_deployer: str address of an additional ERC20 deployer.
        :param erc721_uri: str URL of the ERC721 token.
        :param erc20_tokens_data: list of ERC20CreateData necessary for deploying ERC20 tokens for different services.
        :param deployed_erc20_tokens: list of ERC20 tokens which are already deployed.
        :param encrypt_flag: bool for encryption of the DDO.
        :param compress_flag: bool for compression of the DDO.
        :return: DDO instance
        """
        self._assert_ddo_metadata(metadata)

        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config)

        address = get_address_of_type(self._config, ERC721FactoryContract.CONTRACT_NAME)
        erc721_factory = ERC721FactoryContract(self._web3, address)

        if not erc721_address:
            name = erc721_name or metadata["name"]
            symbol = erc721_symbol or name
            additional_erc20_deployer = erc721_additional_erc_deployer or ZERO_ADDRESS
            token_uri = erc721_uri or "https://oceanprotocol.com/nft/"
            # register on-chain
            tx_id = erc721_factory.deploy_erc721_contract(
                (name, symbol, template_index, additional_erc20_deployer, token_uri),
                from_wallet=publisher_wallet,
            )
            tx_receipt = self._web3.eth.wait_for_transaction_receipt(tx_id)
            registered_event = erc721_factory.get_event_log(
                ERC721FactoryContract.EVENT_NFT_CREATED,
                tx_receipt.blockNumber,
                self._web3.eth.block_number,
                None,
            )
            erc721_address = registered_event[0].args.newTokenAddress
            erc721_token = ERC721Token(self._web3, erc721_address)
            if not erc721_token:
                logger.warning("Creating new datatoken failed.")
                return None
            logger.info(
                f"Successfully created datatoken with address "
                f"{erc721_token.address}."
            )
        else:
            # verify nft address
            if not erc721_factory.verify_nft(erc721_address):
                raise ContractNotFound(
                    f"NFT address {erc721_address} is not found in the ERC721Factory events."
                )

        assert erc721_address, "nft_address is required for publishing a dataset asset."
        erc721_token = ERC721Token(self._web3, erc721_address)

        # Create a DDO object
        asset = Asset()

        # Generating the did and adding to the ddo.
        did = f"did:op:{create_checksum(erc721_token.address + str(self._web3.eth.chain_id))}"
        asset.did = did
        # Check if it's already registered first!
        if self._aquarius.ddo_exists(did):
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )
        asset.chain_id = self._web3.eth.chain_id
        asset.metadata = metadata

        asset.credentials = credentials if credentials else {"allow": [], "deny": []}

        erc20_addresses = []
        services = services or []
        deployed_erc20_tokens = deployed_erc20_tokens or []
        if not deployed_erc20_tokens:
            for erc20_token_data in erc20_tokens_data:
                erc20_addresses.append(
                    self.deploy_datatoken(
                        erc721_factory=erc721_factory,
                        erc721_token=erc721_token,
                        erc20_data=erc20_token_data,
                        from_wallet=publisher_wallet,
                    )
                )
            if not services:
                for erc20_address in erc20_addresses:
                    services = self._add_defaults(
                        services, erc20_address, encrypted_files, provider_uri
                    )
            for erc20_token_address in erc20_addresses:
                deployed_erc20_tokens.append(
                    ERC20Token(self._web3, erc20_token_address)
                )

            datatokens = self.build_datatokens_list(
                services=services, deployed_erc20_tokens=deployed_erc20_tokens
            )
        else:
            if not services:
                for erc20_token in deployed_erc20_tokens:
                    services = self._add_defaults(
                        services, erc20_token.address, encrypted_files, provider_uri
                    )

            datatokens = self.build_datatokens_list(
                services=services, deployed_erc20_tokens=deployed_erc20_tokens
            )

        asset.nft_address = erc721_address
        asset.datatokens = datatokens

        for service in services:
            asset.add_service(service)

        # Validation by Aquarius
        validation_result, validation_errors = self.validate(asset)
        if not validation_result:
            msg = f"Asset has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        document, flags, ddo_hash = self._encrypt_ddo(
            asset, provider_uri, encrypt_flag, compress_flag
        )

        chain_metadata = ChainMetadata(
            metadata_state=0,
            metadata_decryptor_url=provider_uri,
            metadata_decryptor_address=publisher_wallet.address,
            flags=flags,
            data=document,
            data_hash=ddo_hash,
            data_proofs=[],
        )

        erc721_token.set_metadata(chain_metadata, from_wallet=publisher_wallet)

        # Fetch the asset on chain
        asset = self._aquarius.wait_for_asset(did)

        return asset

    def update(
        self,
        asset: Asset,
        publisher_wallet: Wallet,
        provider_uri: Optional[str] = None,
        encrypt_flag: Optional[bool] = False,
        compress_flag: Optional[bool] = False,
    ) -> Optional[Asset]:
        """Update an asset on-chain.

        :param asset: The updated asset to update on-chain
        :param publisher_wallet: Wallet of the publisher updating this asset.
        :param provider_uri: str URL of service provider. This will be used as base to construct the serviceEndpoint for the `access` (download) service
        :param encrypt_flag: bool for encryption of the DDO.
        :param compress_flag: bool for compression of the DDO.
        :return: Optional[Asset] the updated Asset or None if updated asset not found in metadata cache
        """

        self._assert_ddo_metadata(asset.metadata)

        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config)

        address = get_address_of_type(self._config, ERC721FactoryContract.CONTRACT_NAME)
        erc721_factory = ERC721FactoryContract(self._web3, address)
        erc721_address = asset.nft_address

        # Verify nft address
        if not erc721_factory.verify_nft(erc721_address):
            raise ContractNotFound(
                f"NFT address {erc721_address} is not found in the ERC721Factory events."
            )

        assert erc721_address, "nft_address is required for publishing a dataset asset."
        erc721_token = ERC721Token(self._web3, erc721_address)

        assert asset.chain_id == self._web3.eth.chain_id, "Chain id mismatch."

        # Validation by Aquarius
        validation_result, validation_errors = self.validate(asset)
        if not validation_result:
            msg = f"Asset has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        document, flags, ddo_hash = self._encrypt_ddo(
            asset, provider_uri, encrypt_flag, compress_flag
        )

        chain_metadata = ChainMetadata(
            metadata_state=0,
            metadata_decryptor_url=provider_uri,
            metadata_decryptor_address=publisher_wallet.address,
            flags=flags,
            data=document,
            data_hash=ddo_hash,
            data_proofs=[],
        )

        tx_result = erc721_token.set_metadata(
            chain_metadata=chain_metadata, from_wallet=publisher_wallet
        )

        self._web3.eth.wait_for_transaction_receipt(tx_result)

        return self._aquarius.wait_for_asset_update(asset, tx_result)

    @enforce_types
    def resolve(self, did: str) -> "Asset":
        return self._aquarius.get_asset_ddo(did)

    @enforce_types
    def search(self, text: str) -> list:
        """
        Search an asset in oceanDB using aquarius.
        :param text: String with the value that you are searching
        :return: List of assets that match with the query
        """
        logger.info(f"Searching asset containing: {text}")
        return [
            Asset.from_dict(ddo_dict["_source"])
            for ddo_dict in self._aquarius.query_search(
                {"query": {"query_string": {"query": text}}}
            )
            if "_source" in ddo_dict
        ]

    @enforce_types
    def query(self, query: dict) -> list:
        """
        Search an asset in oceanDB using search query.
        :param query: dict with query parameters
            (e.g.) https://github.com/oceanprotocol/aquarius/blob/develop/docs/for_api_users/API.md
        :return: List of assets that match with the query.
        """
        logger.info(f"Searching asset query: {query}")
        return [
            Asset.from_dict(ddo_dict["_source"])
            for ddo_dict in self._aquarius.query_search(query)
            if "_source" in ddo_dict
        ]

    @enforce_types
    def download_asset(
        self,
        asset: Asset,
        provider_uri: str,
        consumer_wallet: Wallet,
        destination: str,
        order_tx_id: str,
        index: Optional[int] = None,
        userdata: Optional[dict] = None,
    ) -> str:

        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")

        service = asset.get_service(ServiceTypes.ASSET_ACCESS)
        assert (
            service and service.type == ServiceTypes.ASSET_ACCESS
        ), f"Service with type {ServiceTypes.ASSET_ACCESS} is not found."

        return download_asset_files(
            asset=asset,
            provider_uri=provider_uri,
            consumer_wallet=consumer_wallet,
            destination=destination,
            order_tx_id=order_tx_id,
            index=index,
            userdata=userdata,
        )

    @enforce_types
    def pay_for_service(
        self,
        asset: Asset,
        service: Service,
        wallet: Wallet,
        initialize_args: Optional[dict] = None,
        consumer_address: Optional[str] = None,
    ):
        dt = ERC20Token(self._web3, service.datatoken)
        balance = dt.balanceOf(wallet.address)

        if not consumer_address:
            consumer_address = wallet.address

        if balance < to_wei(1):
            raise InsufficientBalance(
                f"Your token balance {pretty_ether_and_wei(balance, dt.symbol())} is not sufficient "
                f"to execute the requested service. This service "
                f"requires {pretty_ether_and_wei(1, dt.symbol())}."
            )

        consumable_result = service.is_consumable(
            asset, {"type": "address", "value": wallet.address}
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        data_provider = DataServiceProvider

        built_initialize_args = {
            "did": asset.did,
            "service_id": service.id,
            "consumer_address": consumer_address,
            "service_endpoint": data_provider.build_initialize_endpoint(
                self._config.provider_url
            )[1],
        }

        if initialize_args:
            built_initialize_args.update(initialize_args)

        initialize_response = data_provider.initialize(**built_initialize_args)

        tx_id = dt.start_order(
            consumer=consumer_address,
            service_index=asset.get_index_of_service(service),
            provider_fees=initialize_response.json()["providerFee"],
            from_wallet=wallet,
        )

        return tx_id

    @enforce_types
    def encrypt_files(self, files: list):
        data_provider = DataServiceProvider

        service_endpoint = data_provider.build_encrypt_endpoint(
            self._config.provider_url
        )[1]

        encrypt_response = data_provider.encrypt(files, service_endpoint)

        return encrypt_response.content.decode("utf-8")

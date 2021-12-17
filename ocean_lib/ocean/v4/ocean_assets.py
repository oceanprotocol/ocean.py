#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import copy
import json
import logging
import os
from typing import Optional, Tuple, Type

from enforce_typing import enforce_types
from ocean_lib.agreements.service_types import ServiceTypesV4
from ocean_lib.aquarius import Aquarius
from ocean_lib.assets.v4.asset import V4Asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import AquariusError, ContractNotFound
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.services.v4.service import V4Service
from ocean_lib.utils.utilities import create_checksum, get_timestamp
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import build_credentials_dict, wait_for_asset
from tests.resources.helper_functions import get_address_of_type
from web3 import Web3

logger = logging.getLogger("ocean")


@enforce_types
class OceanAssetV4:
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

    def _get_aquarius(self, url: Optional[str] = None) -> Aquarius:
        return Aquarius.get_instance(url or self._metadata_cache_uri)

    def validate(self, asset: V4Asset) -> Tuple[bool, list]:
        """
        Validate that the asset is ok to be stored in aquarius.

        :param asset: V4Asset.
        :return: (bool, list) list of errors, empty if valid
        """
        return self._get_aquarius(self._metadata_cache_uri).validate_asset(asset)

    def _add_defaults(
        self, services: list, data_token: str, files: str, provider_uri: str
    ) -> list:
        has_access_service = any(
            map(lambda s: s.type == ServiceTypesV4.ASSET_ACCESS, services)
        )

        if not has_access_service:
            access_service = self.build_access_service(
                service_id="1",
                service_endpoint=self._data_provider.build_download_endpoint(
                    provider_uri
                )[1],
                data_token=data_token,
                files=files,
            )

            services.append(access_service)

        return services

    @staticmethod
    def build_access_service(
        service_id: str,
        service_endpoint: str,
        data_token: str,
        files: str,
        timeout: Optional[int] = 3600,
    ) -> V4Service:

        return V4Service(
            service_id=service_id,
            service_type=ServiceTypesV4.ASSET_ACCESS,
            service_endpoint=service_endpoint,
            data_token=data_token,
            files=files,
            timeout=timeout,
        )

    def deploy_datatoken(
        self,
        erc721_factory: ERC721FactoryContract,
        erc721_token: ERC721Token,
        erc20_data: ErcCreateData,
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

    def create(
        self,
        metadata: dict,
        publisher_wallet: Wallet,
        files: str,
        services: Optional[list] = None,
        credentials: Optional[list] = None,
        provider_uri: Optional[str] = None,
        nft_address: Optional[str] = None,
        created: Optional[str] = None,
        nft_name: Optional[str] = None,
        nft_symbol: Optional[str] = None,
        template_index: Optional[int] = 1,
        nft_additional_erc_deployer: Optional[str] = None,
        nft_uri: Optional[str] = None,
        erc20_data: Optional[ErcCreateData] = None,
    ) -> Optional[V4Asset]:
        assert isinstance(
            metadata, dict
        ), f"Expected metadata of type dict, got {type(metadata)}"

        # copy metadata so we don't change the original
        metadata_copy = copy.deepcopy(metadata)

        asset_type = metadata_copy["type"]
        assert asset_type in (
            "dataset",
            "algorithm",
        ), f"Invalid/unsupported asset type {asset_type}"

        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config)

        address = get_address_of_type(self._config, ERC721FactoryContract.CONTRACT_NAME)
        erc721_factory = ERC721FactoryContract(self._web3, address)

        if not nft_address:
            name = nft_name or metadata["name"]
            symbol = nft_symbol or name
            additional_erc20_deployer = nft_additional_erc_deployer or ZERO_ADDRESS
            token_uri = nft_uri or "https://oceanprotocol.com/nft/"
            # register on-chain
            tx_id = erc721_factory.deploy_erc721_contract(
                name,
                symbol,
                template_index=template_index,
                additional_erc20_deployer=additional_erc20_deployer,
                token_uri=token_uri,
                from_wallet=publisher_wallet,
            )
            created = get_timestamp()
            _ = self._web3.eth.wait_for_transaction_receipt(tx_id)
            erc721_token = ERC721Token(
                self._web3, erc721_factory.get_token_address(tx_id)
            )
            if not erc721_token:
                logger.warning("Creating new data token failed.")
                return None
            logger.info(
                f"Successfully created data token with address "
                f"{erc721_token.address} for new dataset asset."
            )
            nft_address = erc721_token.address
        else:
            # verify nft address
            if not erc721_factory.verify_nft(nft_address):
                raise ContractNotFound(
                    f"NFT address {nft_address} is not found in the ERC721Factory events."
                )

        assert nft_address, "nft_address is required for publishing a dataset asset."
        erc721_token = ERC721Token(self._web3, nft_address)

        erc20_address = self.deploy_datatoken(
            erc721_factory=erc721_factory,
            erc721_token=erc721_token,
            erc20_data=erc20_data,
            from_wallet=publisher_wallet,
        )

        services = services or []
        services = self._add_defaults(services, erc20_address, files, provider_uri)
        # Create a DDO object
        asset = V4Asset()

        # Generating the did and adding to the ddo.
        did = f"did:op:{create_checksum(erc721_token.address + str(self._web3.eth.chain_id))}"
        asset.did = did
        # Check if it's already registered first!
        if self._get_aquarius().ddo_exists(did):
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )
        asset.chain_id = self._web3.eth.chain_id
        asset.metadata = metadata
        for service in services:
            asset.add_service(service)

        asset.credentials = credentials if credentials else build_credentials_dict()

        # Validation by Aquarius
        validation_result, validation_errors = self.validate(asset)
        if not validation_result:
            msg = f"Asset has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        nft = {
            "address": erc721_token.address,
            "name": nft_name,
            "symbol": nft_symbol,
            "owner": publisher_wallet.address,
            "state": 0,
            "created": created,
        }
        asset.nft = nft

        data_tokens = [
            {
                "address": erc20_address,
                "name": erc20_data.strings[0],
                "symbol": erc20_data.strings[1],
                "serviceId": service.id,
            }
            for service in services
        ]
        asset.datatokens = data_tokens

        asset_dict = asset.as_dictionary()
        ddo_string = json.dumps(asset_dict)
        ddo_bytes = ddo_string.encode("utf-8")
        encrypted_ddo = ddo_bytes
        ddo_hash = create_checksum(ddo_string)

        _ = erc721_token.set_metadata(
            metadata_state=0,
            metadata_decryptor_url=provider_uri,
            metadata_decryptor_address=publisher_wallet.address,
            flags=bytes([0]),
            data=encrypted_ddo,
            data_hash=ddo_hash,
            from_wallet=publisher_wallet,
        )

        asset = wait_for_asset(self._metadata_cache_uri, did)

        return asset

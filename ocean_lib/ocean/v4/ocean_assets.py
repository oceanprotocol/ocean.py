#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import copy
import logging
import os
from typing import Optional, Type, Tuple

from eth_utils import remove_0x_prefix
from web3 import Web3

from ocean_lib.agreements.service_types import ServiceTypesV4
from ocean_lib.assets.v4.asset import V4Asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import ContractNotFound, AquariusError
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.services.v4.service import V4Service
from enforce_typing import enforce_types

from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.helper_functions import get_address_of_type

logger = logging.getLogger("ocean")


@enforce_types
class OceanAssetV4:
    """Ocean asset class for V4."""

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

    def validate(self, metadata: dict) -> Tuple[bool, list]:
        """
        Validate that the metadata is ok to be stored in aquarius.

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :return: (bool, list) list of errors, empty if valid
        """
        return self._get_aquarius(self._metadata_cache_uri).validate_metadata(metadata)

    def _add_defaults(
        self, services: list, data_token: str, files: str, provider_uri: str
    ) -> list:

        has_access_service = False
        for service in services:
            if service.type == ServiceTypesV4.ASSET_ACCESS:
                has_access_service = True

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

    def create(
        self,
        metadata: dict,
        publisher_wallet: Wallet,
        services: list,
        nft_address: str,
        files: str,
        provider_uri: Optional[str] = None,
        nft_name: Optional[str] = None,
        nft_symbol: Optional[str] = None,
        template_index: Optional[int] = 1,
        nft_additional_erc_deployer: Optional[str] = None,
        nft_uri: Optional[str] = None,
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

        validation_result, validation_errors = self.validate(metadata)
        if not validation_result:
            msg = f"Metadata has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config)

        services = services or []
        services = self._add_defaults(services, nft_address, files, provider_uri)
        # Create a DDO object
        asset = V4Asset()

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
            _ = self._web3.eth.wait_for_transaction_receipt(tx_id)
            nft = ERC721Token(self._web3, erc721_factory.get_token_address(tx_id))
            if not nft:
                logger.warning("Creating new data token failed.")
                return None
            logger.info(
                f"Successfully created data token with address "
                f"{nft.address} for new dataset asset."
            )
        else:
            # verify nft address
            if not erc721_factory.verify_nft(nft_address):
                raise ContractNotFound(
                    f"NFT address {nft_address} is not found in the ERC721Factory events."
                )

        assert nft_address, "nft_address is required for publishing a dataset asset."

        # Generating the did and adding to the ddo.
        did = f"did:op:{remove_0x_prefix(nft_address)}"
        asset.did = did
        logger.debug(f"Using datatoken address as did: {did}")
        # Check if it's already registered first!
        if self._get_aquarius().ddo_exists(did):
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )

        for service in services:
            asset.add_service(service)

        # TODO: provider endpoint encrypt urls
        # TODO: update this call to setMetaData of the NFT -> Store Metadata role
        # TODO: wait until asset appears in Aqua -> verify if aqua receives it

        return asset

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

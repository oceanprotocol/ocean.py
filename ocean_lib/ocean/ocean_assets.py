#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import json
import logging
import lzma
import os
from datetime import datetime
from typing import List, Optional, Tuple, Type, Union

from brownie import network
from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.aquarius import Aquarius
from ocean_lib.assets.asset_downloader import download_asset_files, is_consumable
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_encryptor import DataEncryptor
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import AquariusError, InsufficientBalance
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.data_nft import DataNFT, DataNFTArguments
from ocean_lib.models.datatoken import Datatoken, DatatokenArguments, TokenFeeInfo
from ocean_lib.ocean.util import create_checksum
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.structures.file_objects import (
    ArweaveFile,
    GraphqlQuery,
    SmartContractCall,
    UrlFile,
)
from ocean_lib.web3_internal.utils import check_network

logger = logging.getLogger("ocean")


class OceanAssets:
    """Ocean asset class for V4."""

    @enforce_types
    def __init__(self, config_dict, data_provider: Type[DataServiceProvider]) -> None:
        """Initialises OceanAssets object."""
        network_name = config_dict["NETWORK_NAME"]
        check_network(network_name)

        self._config_dict = config_dict
        self._chain_id = network.chain.id

        self._metadata_cache_uri = config_dict.get("METADATA_CACHE_URI")
        self._data_provider = data_provider

        downloads_path = os.path.join(os.getcwd(), "downloads")
        self._downloads_path = config_dict.get("DOWNLOADS_PATH", downloads_path)
        self._aquarius = Aquarius.get_instance(self._metadata_cache_uri)

    @enforce_types
    def validate(self, ddo: DDO) -> Tuple[bool, list]:
        """
        Validate that the ddo is ok to be stored in aquarius.

        :param ddo: DDO.
        :return: (bool, list) list of errors, empty if valid
        """
        # Validation by Aquarius
        validation_result, validation_errors = self._aquarius.validate_ddo(ddo)
        if not validation_result:
            msg = f"DDO has validation errors: {validation_errors}"
            logger.error(msg)
            raise ValueError(msg)

        return validation_result, validation_errors

    @staticmethod
    @enforce_types
    def _encrypt_ddo(
        ddo: DDO,
        provider_uri: str,
        encrypt_flag: Optional[bool] = True,
        compress_flag: Optional[bool] = True,
    ):
        # Process the DDO
        ddo_dict = ddo.as_dictionary()
        ddo_string = json.dumps(ddo_dict, separators=(",", ":"))
        ddo_bytes = ddo_string.encode("utf-8")
        ddo_hash = create_checksum(ddo_string)

        # Plain DDO
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
            encrypt_response = DataEncryptor.encrypt(
                objects_to_encrypt=ddo_string, provider_uri=provider_uri
            )
            document = encrypt_response.text
            return document, flags, ddo_hash

        # Encrypted & compressed
        flags = bytes([3])
        # Compress DDO
        compressed_document = lzma.compress(ddo_bytes)

        # Encrypt DDO
        encrypt_response = DataEncryptor.encrypt(
            objects_to_encrypt=compressed_document, provider_uri=provider_uri
        )

        document = encrypt_response.text

        return document, flags, ddo_hash

    @staticmethod
    @enforce_types
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

    @enforce_types
    def create_algo_asset(
        self,
        name: str,
        url: str,
        publisher_wallet,
        image: str = "oceanprotocol/algo_dockers",
        tag: str = "python-branin",
        checksum: str = "sha256:8221d20c1c16491d7d56b9657ea09082c0ee4a8ab1a6621fa720da58b09580e4",
        wait_for_aqua: bool = True,
    ) -> tuple:
        """Create asset of type "algorithm", having UrlFiles, with good defaults"""

        if image == "oceanprotocol/algo_dockers" or tag == "python-branin":
            assert image == "oceanprotocol/algo_dockers" and tag == "python-branin"

        metadata = self._default_metadata(name, publisher_wallet, "algorithm")
        metadata["algorithm"] = {
            "language": "python",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": image,
                "tag": tag,
                "checksum": checksum,
            },
        }

        files = [UrlFile(url)]
        return self._create_1dt(metadata, files, publisher_wallet, wait_for_aqua)

    @enforce_types
    def create_url_asset(
        self, name: str, url: str, publisher_wallet, wait_for_aqua: bool = True
    ) -> tuple:
        """Create asset of type "data", having UrlFiles, with good defaults"""
        metadata = self._default_metadata(name, publisher_wallet)
        files = [UrlFile(url)]
        return self._create_1dt(metadata, files, publisher_wallet, wait_for_aqua)

    @enforce_types
    def create_arweave_asset(
        self,
        name: str,
        transaction_id: str,
        publisher_wallet,
        wait_for_aqua: bool = True,
    ) -> tuple:
        """Create asset of type "data", having UrlFiles, with good defaults"""
        metadata = self._default_metadata(name, publisher_wallet)
        files = [ArweaveFile(transaction_id)]
        return self._create_1dt(metadata, files, publisher_wallet, wait_for_aqua)

    @enforce_types
    def create_graphql_asset(
        self,
        name: str,
        url: str,
        query: str,
        publisher_wallet,
        wait_for_aqua: bool = True,
    ) -> tuple:
        """Create asset of type "data", having GraphqlQuery files, w good defaults"""
        metadata = self._default_metadata(name, publisher_wallet)
        files = [GraphqlQuery(url, query)]
        return self._create_1dt(metadata, files, publisher_wallet, wait_for_aqua)

    @enforce_types
    def create_onchain_asset(
        self,
        name: str,
        contract_address: str,
        contract_abi: dict,
        publisher_wallet,
        wait_for_aqua: bool = True,
    ) -> tuple:
        """Create asset of type "data", having SmartContractCall files, w defaults"""
        chain_id = self._chain_id
        onchain_data = SmartContractCall(contract_address, chain_id, contract_abi)
        files = [onchain_data]
        metadata = self._default_metadata(name, publisher_wallet)
        return self._create_1dt(metadata, files, publisher_wallet, wait_for_aqua)

    @enforce_types
    def _default_metadata(self, name: str, publisher_wallet, type="dataset") -> dict:
        date_created = datetime.now().isoformat()
        metadata = {
            "created": date_created,
            "updated": date_created,
            "description": name,
            "name": name,
            "type": type,
            "author": publisher_wallet.address[:7],
            "license": "CC0: PublicDomain",
        }
        return metadata

    @enforce_types
    def _create_1dt(self, metadata, files, publisher_wallet, wait_for_aqua):
        """Call create(), focusing on just one datatoken"""
        name = metadata["name"]
        (data_nft, datatokens, ddo) = self.create(
            metadata,
            publisher_wallet,
            datatoken_args=[DatatokenArguments(f"{name}: DT1", files=files)],
            wait_for_aqua=wait_for_aqua,
        )
        datatoken = None if datatokens is None else datatokens[0]
        return (data_nft, datatoken, ddo)

    # Don't enforce types due to error:
    # TypeError: Subscripted generics cannot be used with class and instance checks
    def create(
        self,
        metadata: dict,
        publisher_wallet,
        credentials: Optional[dict] = None,
        data_nft_address: Optional[str] = None,
        data_nft_args: Optional[DataNFTArguments] = None,
        deployed_datatokens: Optional[List[Datatoken]] = None,
        services: Optional[list] = None,
        datatoken_args: Optional[List["DatatokenArguments"]] = None,
        encrypt_flag: Optional[bool] = True,
        compress_flag: Optional[bool] = True,
        wait_for_aqua: bool = True,
    ) -> Optional[DDO]:
        """Register an asset on-chain. Asset = {data_NFT, >=0 datatokens, DDO}

        Creating/deploying a DataNFT contract and in the Metadata store (Aquarius).

        :param metadata: dict conforming to the Metadata accepted by Ocean Protocol.
        :param publisher_wallet: account of the publisher registering this asset.
        :param credentials: credentials dict necessary for the asset.
        construct the serviceEndpoint for the `access` (download) service
        :param data_nft_address: hex str the address of the data NFT. The new
        asset will be associated with this data NFT address.
        :param data_nft_args: object of DataNFTArguments type if creating a new one
        :param deployed_datatokens: list of datatokens which are already deployed.
        :param encrypt_flag: bool for encryption of the DDO.
        :param compress_flag: bool for compression of the DDO.
        :param wait_for_aqua: wait to ensure ddo's updated in aquarius?
        :return: tuple of (data_nft, datatokens, ddo)
        """
        self._assert_ddo_metadata(metadata)

        provider_uri = DataServiceProvider.get_url(self._config_dict)

        if not data_nft_address:
            data_nft_args = data_nft_args or DataNFTArguments(
                metadata["name"], metadata["name"]
            )
            data_nft = data_nft_args.deploy_contract(
                self._config_dict, publisher_wallet
            )
            # register on-chain
            if not data_nft:
                logger.warning("Creating new NFT failed.")
                return None, None, None
            logger.info(f"Successfully created NFT with address {data_nft.address}.")
        else:
            data_nft = DataNFT(self._config_dict, data_nft_address)

        # Create DDO object
        ddo = DDO()

        # Generate the did, add it to the ddo.
        did = f"did:op:{create_checksum(data_nft.address + str(self._chain_id))}"
        ddo.did = did
        # Check if it's already registered first!
        if self._aquarius.ddo_exists(did):
            raise AquariusError(
                f"Asset id {did} is already registered to another asset."
            )
        ddo.chain_id = self._chain_id
        ddo.metadata = metadata

        ddo.credentials = credentials if credentials else {"allow": [], "deny": []}

        ddo.nft_address = data_nft.address
        datatokens = []

        if not deployed_datatokens:
            services = []
            for datatoken_arg in datatoken_args:
                new_dt = datatoken_arg.create_datatoken(
                    data_nft, publisher_wallet, with_services=True
                )
                datatokens.append(new_dt)

                services.extend(datatoken_arg.services)

            for service in services:
                ddo.add_service(service)
        else:
            if not services:
                logger.warning("services required with deployed_datatokens.")
                return None, None, None

            datatokens = deployed_datatokens
            dt_addresses = []
            for datatoken in datatokens:
                if deployed_datatokens[0].address not in data_nft.getTokensList():
                    logger.warning(
                        "some deployed_datatokens don't belong to the given data nft."
                    )
                    return None, None, None

                dt_addresses.append(datatoken.address)

            for service in services:
                if service.datatoken not in dt_addresses:
                    logger.warning("Datatoken services mismatch.")
                    return None, None, None

                ddo.add_service(service)

        # Validation by Aquarius
        _, proof = self.validate(ddo)
        proof = (
            proof["publicKey"],
            proof["v"],
            proof["r"][0],
            proof["s"][0],
        )

        document, flags, ddo_hash = self._encrypt_ddo(
            ddo, provider_uri, encrypt_flag, compress_flag
        )

        data_nft.setMetaData(
            0,
            provider_uri,
            Web3.toChecksumAddress(publisher_wallet.address.lower()).encode("utf-8"),
            flags,
            document,
            ddo_hash,
            [proof],
            {"from": publisher_wallet},
        )

        # Fetch the ddo on chain
        if wait_for_aqua:
            ddo = self._aquarius.wait_for_ddo(did)

        return (data_nft, datatokens, ddo)

    @enforce_types
    def update(
        self,
        ddo: DDO,
        publisher_wallet,
        provider_uri: Optional[str] = None,
        encrypt_flag: Optional[bool] = True,
        compress_flag: Optional[bool] = True,
    ) -> Optional[DDO]:
        """Update a ddo on-chain.

        :param ddo - DDO to update
        :param publisher_wallet - who published this ddo
        :param provider_uri - URL of service provider. This will be used as base to construct the serviceEndpoint for the `access` (download) service
        :param encrypt_flag - encrypt this DDO?
        :param compress_flag - compress this DDO?
        :return - the updated DDO, or None if updated ddo not found in aquarius
        """
        self._assert_ddo_metadata(ddo.metadata)

        if not provider_uri:
            provider_uri = DataServiceProvider.get_url(self._config_dict)

        assert ddo.nft_address, "need nft address to update a ddo"
        data_nft = DataNFT(self._config_dict, ddo.nft_address)

        assert ddo.chain_id == self._chain_id

        for service in ddo.services:
            service.encrypt_files(ddo.nft_address)

        # Validation by Aquarius
        validation_result, errors_or_proof = self.validate(ddo)
        if not validation_result:
            msg = f"DDO has validation errors: {errors_or_proof}"
            logger.error(msg)
            raise ValueError(msg)

        document, flags, ddo_hash = self._encrypt_ddo(
            ddo, provider_uri, encrypt_flag, compress_flag
        )

        proof = (
            errors_or_proof["publicKey"],
            errors_or_proof["v"],
            errors_or_proof["r"][0],
            errors_or_proof["s"][0],
        )

        tx_result = data_nft.setMetaData(
            0,
            provider_uri,
            Web3.toChecksumAddress(publisher_wallet.address.lower()).encode("utf-8"),
            flags,
            document,
            ddo_hash,
            [proof],
            {"from": publisher_wallet},
        )

        ddo = self._aquarius.wait_for_ddo_update(ddo, tx_result.txid)

        return ddo

    @enforce_types
    def resolve(self, did: str) -> "DDO":
        return self._aquarius.get_ddo(did)

    @enforce_types
    def search(self, text: str) -> list:
        """
        Search for DDOs in aquarius that contain the target text string
        :param text - target string
        :return - List of DDOs that match with the query
        """
        logger.info(f"Search for DDOs containing text: {text}")
        text = text.replace(":", "\\:").replace("\\\\:", "\\:")
        return [
            DDO.from_dict(ddo_dict["_source"])
            for ddo_dict in self._aquarius.query_search(
                {"query": {"query_string": {"query": text}}}
            )
            if "_source" in ddo_dict
        ]

    @enforce_types
    def query(self, query: dict) -> list:
        """
        Search for DDOs in aquarius with a search query dict
        :param query - dict with query parameters
          More info at: https://docs.oceanprotocol.com/api-references/aquarius-rest-api
        :return - List of DDOs that match the query.
        """
        logger.info(f"Search for DDOs matching query: {query}")
        return [
            DDO.from_dict(ddo_dict["_source"])
            for ddo_dict in self._aquarius.query_search(query)
            if "_source" in ddo_dict
        ]

    @enforce_types
    def download_asset(
        self,
        ddo: DDO,
        consumer_wallet,
        destination: str,
        order_tx_id: Union[str, bytes],
        service: Optional[Service] = None,
        index: Optional[int] = None,
        userdata: Optional[dict] = None,
    ) -> str:
        service = service or ddo.services[0]  # fill in good default

        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")

        assert (
            service and service.type == ServiceTypes.ASSET_ACCESS
        ), f"Service with type {ServiceTypes.ASSET_ACCESS} is not found."

        path: str = download_asset_files(
            ddo, service, consumer_wallet, destination, order_tx_id, index, userdata
        )
        return path

    @enforce_types
    def pay_for_access_service(
        self,
        ddo: DDO,
        wallet,
        service: Optional[Service] = None,
        consume_market_fees: Optional[TokenFeeInfo] = None,
        consumer_address: Optional[str] = None,
        userdata: Optional[dict] = None,
    ):
        # fill in good defaults as needed
        service = service or ddo.services[0]
        consumer_address = consumer_address or wallet.address

        # main work...
        dt = Datatoken(self._config_dict, service.datatoken)
        balance = dt.balanceOf(wallet.address)

        if balance < Web3.toWei(1, "ether"):
            raise InsufficientBalance(
                f"Your token balance {balance} {dt.symbol()} is not sufficient "
                f"to execute the requested service. This service "
                f"requires 1 wei."
            )

        consumable_result = is_consumable(
            ddo,
            service,
            {"type": "address", "value": wallet.address},
            userdata=userdata,
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        data_provider = DataServiceProvider

        initialize_args = {
            "did": ddo.did,
            "service": service,
            "consumer_address": consumer_address,
        }

        initialize_response = data_provider.initialize(**initialize_args)
        provider_fees = initialize_response.json()["providerFee"]

        receipt = dt.start_order(
            consumer=consumer_address,
            service_index=ddo.get_index_of_service(service),
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            transaction_parameters={"from": wallet},
        )

        return receipt.txid

    @enforce_types
    def pay_for_compute_service(
        self,
        datasets: List[ComputeInput],
        algorithm_data: Union[ComputeInput, AlgorithmMetadata],
        compute_environment: str,
        valid_until: int,
        consume_market_order_fee_address: str,
        wallet,
        consumer_address: Optional[str] = None,
    ):
        data_provider = DataServiceProvider

        if not consumer_address:
            consumer_address = wallet.address

        initialize_response = data_provider.initialize_compute(
            [x.as_dictionary() for x in datasets],
            algorithm_data.as_dictionary(),
            datasets[0].service.service_endpoint,
            consumer_address,
            compute_environment,
            valid_until,
        )

        result = initialize_response.json()
        for i, item in enumerate(result["datasets"]):
            self._start_or_reuse_order_based_on_initialize_response(
                datasets[i],
                item,
                TokenFeeInfo(
                    consume_market_order_fee_address,
                    datasets[i].consume_market_order_fee_token,
                    datasets[i].consume_market_order_fee_amount,
                ),
                wallet,
                consumer_address,
            )

        if "algorithm" in result:
            self._start_or_reuse_order_based_on_initialize_response(
                algorithm_data,
                result["algorithm"],
                TokenFeeInfo(
                    address=consume_market_order_fee_address,
                    token=algorithm_data.consume_market_order_fee_token,
                    amount=algorithm_data.consume_market_order_fee_amount,
                ),
                wallet,
                consumer_address,
            )

            return datasets, algorithm_data

        return datasets, None

    @enforce_types
    def _start_or_reuse_order_based_on_initialize_response(
        self,
        asset_compute_input: ComputeInput,
        item: dict,
        consume_market_fees: TokenFeeInfo,
        wallet,
        consumer_address: Optional[str] = None,
    ):
        provider_fees = item.get("providerFee")
        valid_order = item.get("validOrder")

        if valid_order and not provider_fees:
            asset_compute_input.transfer_tx_id = valid_order
            return

        service = asset_compute_input.service
        dt = Datatoken(self._config_dict, service.datatoken)

        if valid_order and provider_fees:
            asset_compute_input.transfer_tx_id = dt.reuse_order(
                valid_order,
                provider_fees=provider_fees,
                transaction_parameters={"from": wallet},
            ).txid
            return

        asset_compute_input.transfer_tx_id = dt.start_order(
            consumer=consumer_address,
            service_index=asset_compute_input.ddo.get_index_of_service(service),
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            transaction_parameters={"from": wallet},
        ).txid

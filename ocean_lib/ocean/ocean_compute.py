#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from enforce_typing import enforce_types
from eth_account.messages import encode_defunct

from ocean_lib.assets.asset import V3Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.assets.trusted_algorithms import create_publisher_trusted_algorithms
from ocean_lib.common.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger("ocean")


class OceanCompute:

    """Ocean assets class."""

    @enforce_types
    def __init__(
        self, config: Union[Config, Dict], data_provider: Type[DataServiceProvider]
    ) -> None:
        """Initialises OceanCompute class."""
        self._config = config
        self._data_provider = data_provider

    @staticmethod
    @enforce_types
    def build_cluster_attributes(cluster_type: str, url: str) -> Dict[str, str]:
        """
        Builds cluster attributes.

        :param cluster_type: str (e.g. Kubernetes)
        :param url: str (e.g. http://10.0.0.17/xxx)
        :return:
        """
        return {"type": cluster_type, "url": url}

    @staticmethod
    @enforce_types
    def build_container_attributes(
        image: str, tag: str, entrypoint: str
    ) -> Dict[str, str]:
        """
        Builds container attributes.

        :param image: str name of Docker image (e.g. node)
        :param tag: str the Docker image tag (e.g. latest or a specific version number)
        :param entrypoint: str executable file (e.g. node $ALGO)
        :return:
        """
        return {"image": image, "tag": tag, "entrypoint": entrypoint}

    @staticmethod
    @enforce_types
    def build_server_attributes(
        server_id: str,
        server_type: str,
        cpu: int,
        gpu: int,
        memory: str,
        disk: str,
        max_run_time: int,
    ) -> Dict[str, Union[int, str]]:
        """
        Builds server attributes.

        :param server_id: str
        :param server_type: str
        :param cpu: integer number of available cpu units
        :param gpu: integer number of available gpu units
        :param memory: str amount of RAM memory (in mb or gb)
        :param disk: str storage capacity (in gb, tb, etc.)
        :param max_run_time: integer maximum allowed run time in seconds
        :return:
        """
        return {
            "serverId": server_id,
            "serverType": server_type,
            "cpu": cpu,
            "gpu": gpu,
            "memory": memory,
            "disk": disk,
            "maxExecutionTime": max_run_time,
        }

    # can not enforce types due to subscripted generics error
    @staticmethod
    def build_service_provider_attributes(
        provider_type: str,
        description: str,
        cluster: Dict[str, str],
        containers: Union[Dict[str, str], List[Dict[str, str]]],
        servers: Union[Dict, List],
    ) -> Dict[str, Any]:
        """
        Return a dict with attributes describing the details of compute resources in this service

        :param provider_type: str type of resource provider such as Azure or AWS
        :param description: str details describing the resource provider
        :param cluster: dict attributes describing the cluster (see `build_cluster_attributes`)
        :param containers: list of dicts each has attributes describing the container (see `build_container_attributes`)
        :param servers: list of dicts each has attributes to describe server (see `build_server_attributes`)
        :return:
        """
        return {
            "type": provider_type,
            "description": description,
            "environment": {
                "cluster": cluster,
                "supportedContainers": containers,
                "supportedServers": servers,
            },
        }

    @staticmethod
    @enforce_types
    def build_service_privacy_attributes(
        trusted_algorithms: Optional[list] = None,
        trusted_algorithm_publishers: Optional[list] = None,
        metadata_cache_uri: Optional[str] = None,
        allow_raw_algorithm: Optional[bool] = False,
        allow_all_published_algorithms: Optional[bool] = False,
        allow_network_access: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        :param trusted_algorithms: list of algorithm did to be trusted by the compute service provider
        :param trusted_algorithm_publishers: list of algorithm publisher (addresses) that can be trusted by the compute service provider
        :param metadata_cache_uir: URI used to get DDOs for trusted algorithm DIDs if trusted_algorithms set
        :param allow_raw_algorithm: bool -- when True, unpublished raw algorithm code can be run on this dataset
        :param allow_all_published_algorithms: bool -- when True, any published algorithm can be run on this dataset
            The list of `trusted_algorithms` will be ignored in this case.
        :param allow_network_access: bool -- allow/disallow the algorithm network access during execution
        :return: dict
        """
        privacy = {
            "allowRawAlgorithm": allow_raw_algorithm,
            "allowAllPublishedAlgorithms": allow_all_published_algorithms,
            "publisherTrustedAlgorithms": [],
            "allowNetworkAccess": allow_network_access,
        }
        if trusted_algorithms:
            privacy["publisherTrustedAlgorithms"] = create_publisher_trusted_algorithms(
                trusted_algorithms, metadata_cache_uri
            )
        if trusted_algorithm_publishers:
            privacy[
                "publisherTrustedAlgorithmPublishers"
            ] = trusted_algorithm_publishers

        return privacy

    @staticmethod
    @enforce_types
    def create_compute_service_attributes(
        timeout: int,
        creator: str,
        date_published: str,
        provider_attributes: Optional[dict] = None,
        privacy_attributes: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """
        Creates compute service attributes.

        :param timeout: integer maximum amount of running compute service in seconds
        :param creator: str ethereum address
        :param date_published: str timestamp (datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
        :param provider_attributes: dict describing the details of the compute resources (see `build_service_provider_attributes`)
        :param privacy_attributes: dict specifying what algorithms can be run in this compute service
        :return: dict with `main` key and value contain the minimum required attributes of a compute service
        """
        if privacy_attributes is None:
            privacy_attributes = OceanCompute.build_service_privacy_attributes()

        for key in [
            "allowRawAlgorithm",
            "allowAllPublishedAlgorithms",
            "allowNetworkAccess",
        ]:
            assert key in privacy_attributes

        assert (
            "publisherTrustedAlgorithms" in privacy_attributes
            or "publisherTrustedAlgorithmPublishers" in privacy_attributes
        )

        attributes = {
            "main": {
                "name": "dataAssetComputingServiceAgreement",
                "creator": creator,
                "datePublished": date_published,
                "cost": 1.0,
                "timeout": timeout,
                "provider": provider_attributes,
                "privacy": privacy_attributes,
            }
        }
        return attributes

    @staticmethod
    @enforce_types
    def _status_from_job_info(job_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper function to extract the status dict with an added boolean for quick validation
        :param job_info: dict having status and statusText keys
        :return:
        """
        return {
            "ok": job_info["status"] not in (31, 32),
            "status": job_info["status"],
            "statusText": job_info["statusText"],
        }

    # can not type check due to Subscripted generics error
    @staticmethod
    def check_output_dict(
        output_def: Optional[Dict[str, Any]],
        consumer_address: str,
        data_provider: DataServiceProvider,
        config: Config,
    ) -> Dict[str, Any]:
        """
        Validate the `output_def` dict and fills in defaults for missing values.

        :param output_def: dict
        :param consumer_address: hex str the consumer ethereum address
        :param data_provider:  DataServiceProvider class or similar interface
        :param config: Config instance
        :return: dict a valid `output_def` object
        """
        default_output_def = {
            "nodeUri": config.network_url,
            "brizoUri": data_provider.get_url(config),
            "brizoAddress": config.provider_address,
            "metadata": dict(),
            "metadataUri": config.metadata_cache_uri,
            "owner": consumer_address,
            "publishOutput": 0,
            "publishAlgorithmLog": 0,
            "whitelist": [],
        }

        output_def = output_def if isinstance(output_def, dict) else dict()
        default_output_def.update(output_def)
        return default_output_def

    @enforce_types
    def _sign_message(
        self,
        wallet: Wallet,
        msg: str,
        nonce: Optional[int] = None,
        service_endpoint: Optional[str] = None,
    ) -> str:
        if nonce is None:
            uri = self._data_provider.get_root_uri(service_endpoint)
            nonce = str(self._data_provider.get_nonce(wallet.address, uri))
        return sign_hash(encode_defunct(text=f"{msg}{nonce}"), wallet)

    @enforce_types
    def start(
        self,
        input_datasets: list,
        consumer_wallet: Wallet,
        nonce: Optional[int] = None,
        algorithm_did: Optional[str] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_tx_id: Optional[str] = None,
        algorithm_data_token: Optional[str] = None,
        output: Optional[dict] = None,
        job_id: Optional[str] = None,
        algouserdata: Optional[dict] = None,
    ) -> str:
        """
        Start a remote compute job on the asset files.

        Files are identified by `did` after verifying that the provider service is active and transferring the
        number of data-tokens required for using this compute service.

        :param input_datasets: list of ComputeInput -- list of input datasets to the compute job. A dataset is
            represented with ComputeInput struct
        :param consumer_wallet: Wallet instance of the consumer ordering the service
        :param nonce: int value to use in the signature
        :param algorithm_did: str -- the asset did (of `algorithm` type) which consist of `did:op:` and
            the assetId hex str (without `0x` prefix)
        :param algorithm_meta: `AlgorithmMetadata` instance -- metadata about the algorithm being run if
            `algorithm` is being used. This is ignored when `algorithm_did` is specified.
        :param algorithm_tx_id: transaction hash of algorithm StartOrder tx (Required when using `algorithm_did`)
        :param algorithm_data_token: datatoken address of this algorithm (Required when using `algorithm_did`)
        :param output: dict object to be used in publishing mechanism, must define
        :param job_id: str identifier of a compute job that was previously started and
            stopped (if supported by the provider's  backend)
        :return: str -- id of compute job being executed
        """
        assert (
            algorithm_did or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        for i in input_datasets:
            assert isinstance(i, ComputeInput)

        first_input = input_datasets[0]
        did = first_input.did
        order_tx_id = first_input.transfer_tx_id
        service_id = first_input.service_id

        output = OceanCompute.check_output_dict(
            output, consumer_wallet.address, self._data_provider, self._config
        )
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        _, service_endpoint = self._get_service_endpoint(did, asset)

        service = asset.get_service_by_index(service_id)
        sa = Service.from_json(service.as_dictionary())
        assert (
            ServiceTypes.CLOUD_COMPUTE == sa.type
        ), "service at serviceId is not of type compute service."

        consumable_result = asset.is_consumable(
            {"type": "address", "value": consumer_wallet.address},
            provider_uri=sa.service_endpoint,
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        signature = self._sign_message(
            consumer_wallet,
            f"{consumer_wallet.address}{did}",
            nonce=nonce,
            service_endpoint=sa.service_endpoint,
        )

        try:
            job_info = self._data_provider.start_compute_job(
                did,
                service_endpoint,
                consumer_wallet.address,
                signature,
                sa.index,
                order_tx_id,
                algorithm_did,
                algorithm_meta,
                algorithm_tx_id,
                algorithm_data_token,
                output,
                input_datasets,
                job_id,
                userdata=first_input.userdata,
                algouserdata=algouserdata,
            )

            return job_info["jobId"]
        except ValueError:
            raise

    @enforce_types
    def status(self, did: str, job_id: str, wallet: Wallet) -> Dict[str, Any]:
        """
        Gets job status.

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for an existing compute job, keys are (ok, status, statusText)
        """
        _, service_endpoint = self._get_service_endpoint(did)
        msg = f'{wallet.address}{job_id or ""}{did}'
        return OceanCompute._status_from_job_info(
            self._data_provider.compute_job_status(
                did,
                job_id,
                service_endpoint,
                wallet.address,
                self._sign_message(wallet, msg, service_endpoint=service_endpoint),
            )
        )

    @enforce_types
    def result(self, did: str, job_id: str, wallet: Wallet) -> Dict[str, Any]:
        """
        Gets job result.

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the results/logs urls for an existing compute job, keys are (did, urls, logs)
        """
        _, service_endpoint = self._get_service_endpoint(did)
        msg = f'{wallet.address}{job_id or ""}{did}'
        info_dict = self._data_provider.compute_job_result(
            did,
            job_id,
            service_endpoint,
            wallet.address,
            self._sign_message(wallet, msg, service_endpoint=service_endpoint),
        )
        return {
            "did": info_dict.get("resultsDid", ""),
            "urls": info_dict.get("resultsUrl", []),
            "logs": info_dict.get("algorithmLogUrl", []),
        }

    @enforce_types
    def result_file(
        self, did: str, job_id: str, index: int, wallet: Wallet
    ) -> Dict[str, Any]:
        """
        Gets job result.

        :param job_id: str id of the compute job
        :param index: compute result index
        :param wallet: Wallet instance
        :return: dict the results/logs urls for an existing compute job, keys are (did, urls, logs)
        """
        _, service_endpoint = self._get_compute_result_file_endpoint(did)
        msg = f"{wallet.address}{job_id}{str(index)}"
        result = self._data_provider.compute_job_result_file(
            job_id,
            index,
            service_endpoint,
            wallet.address,
            self._sign_message(wallet, msg, service_endpoint=service_endpoint),
        )

        return result

    @enforce_types
    def stop(self, did: str, job_id: str, wallet: Wallet) -> Dict[str, Any]:
        """
        Attempt to stop the running compute job.

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for the stopped compute job, keys are (ok, status, statusText)
        """
        _, service_endpoint = self._get_service_endpoint(did)
        msg = f'{wallet.address}{job_id or ""}{did}'
        return self._status_from_job_info(
            self._data_provider.stop_compute_job(
                did,
                job_id,
                service_endpoint,
                wallet.address,
                self._sign_message(wallet, msg, service_endpoint=service_endpoint),
            )
        )

    @enforce_types
    def _get_service_endpoint(
        self, did: str, asset: Optional[V3Asset] = None
    ) -> Tuple[str, str]:
        if not asset:
            asset = resolve_asset(did, self._config.metadata_cache_uri)

        return self._data_provider.build_compute_endpoint(
            asset.get_service(ServiceTypes.CLOUD_COMPUTE).service_endpoint
        )

    @enforce_types
    def _get_compute_result_file_endpoint(
        self, did: str, asset: Optional[V3Asset] = None
    ) -> Tuple[str, str]:
        if not asset:
            asset = resolve_asset(did, self._config.metadata_cache_uri)

        return self._data_provider.build_compute_result_file_endpoint(
            asset.get_service(ServiceTypes.CLOUD_COMPUTE).service_endpoint
        )

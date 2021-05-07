#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Optional

from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.assets.utils import create_publisher_trusted_algorithms
from ocean_lib.common.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_factory import ServiceDescriptor
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger("ocean")


@enforce_types_shim
class OceanCompute:

    """Ocean assets class."""

    def __init__(self, config, data_provider):
        """Initialises OceanCompute class."""
        self._config = config
        self._data_provider = data_provider

    @staticmethod
    def build_cluster_attributes(cluster_type, url):
        """
        Builds cluster attributes.

        :param cluster_type: str (e.g. Kubernetes)
        :param url: str (e.g. http://10.0.0.17/xxx)
        :return:
        """
        return {"type": cluster_type, "url": url}

    @staticmethod
    def build_container_attributes(image, tag, entrypoint):
        """
        Builds container attributes.

        :param image: str name of Docker image (e.g. node)
        :param tag: str the Docker image tag (e.g. latest or a specific version number)
        :param entrypoint: str executable file (e.g. node $ALGO)
        :return:
        """
        return {"image": image, "tag": tag, "entrypoint": entrypoint}

    @staticmethod
    def build_server_attributes(
        server_id, server_type, cpu, gpu, memory, disk, max_run_time
    ):
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

    @staticmethod
    def build_service_provider_attributes(
        provider_type, description, cluster, containers, servers
    ):
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
    def build_service_privacy_attributes(
        trusted_algorithms: list = None,
        allow_raw_algorithm: bool = False,
        allow_all_published_algorithms: bool = False,
        allow_network_access: bool = False,
    ):
        """
        :param trusted_algorithms: list of algorithm did to be trusted by the compute service provider
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
                trusted_algorithms, ConfigProvider.get_config().metadata_cache_uri
            )

        return privacy

    @staticmethod
    def create_compute_service_attributes(
        timeout: int,
        creator: str,
        date_published: str,
        provider_attributes: dict = None,
        privacy_attributes: dict = None,
    ):
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

        assert set(privacy_attributes.keys()) == {
            "allowRawAlgorithm",
            "allowAllPublishedAlgorithms",
            "publisherTrustedAlgorithms",
            "allowNetworkAccess",
        }

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
    def _status_from_job_info(job_info):
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

    @staticmethod
    def check_output_dict(output_def, consumer_address, data_provider, config=None):
        """
        Validate the `output_def` dict and fills in defaults for missing values.

        :param output_def: dict
        :param consumer_address: hex str the consumer ethereum address
        :param data_provider:  DataServiceProvider class or similar interface
        :param config: Config instance
        :return: dict a valid `output_def` object
        """
        if not config:
            config = ConfigProvider.get_config()

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

    def create_compute_service_descriptor(self, attributes):
        """
        Return a service descriptor (tuple) for service of type ServiceTypes.CLOUD_COMPUTE
        and having the required attributes and service endpoint.

        :param attributes: dict as created in `create_compute_service_attributes`
        """
        compute_endpoint = self._data_provider.get_url(self._config)
        return ServiceDescriptor.compute_service_descriptor(
            attributes=attributes, service_endpoint=compute_endpoint
        )

    def _sign_message(self, wallet, msg, nonce=None, service_endpoint=None):
        if nonce is None:
            uri = self._data_provider.get_root_uri(service_endpoint)
            nonce = self._data_provider.get_nonce(wallet.address, uri)
        return sign_hash(add_ethereum_prefix_and_hash_msg(f"{msg}{nonce}"), wallet)

    def start(
        self,
        input_datasets: list,
        consumer_wallet: Wallet,
        nonce: Optional[int] = None,
        algorithm_did: Optional[str] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_tx_id: str = None,
        algorithm_data_token: str = None,
        output: dict = None,
        job_id: str = None,
    ):
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
            output, consumer_wallet.address, data_provider=self._data_provider
        )
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        _, service_endpoint = self._get_service_endpoint(did, asset)

        service = asset.get_service_by_index(service_id)
        sa = ServiceAgreement.from_json(service.as_dictionary())
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
            )

            return job_info["jobId"]
        except ValueError:
            raise

    def status(self, did, job_id, wallet):
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

    def result(self, did, job_id, wallet):
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

    def stop(self, did, job_id, wallet):
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

    def _get_service_endpoint(self, did, asset=None):
        if not asset:
            asset = resolve_asset(did, self._config.metadata_cache_uri)

        return self._data_provider.build_compute_endpoint(
            ServiceAgreement.from_ddo(
                ServiceTypes.CLOUD_COMPUTE, asset
            ).service_endpoint
        )

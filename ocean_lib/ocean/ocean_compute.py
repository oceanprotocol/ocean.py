import logging

from ocean_utils.agreements.service_factory import ServiceDescriptor
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.agreements.service_agreement import ServiceAgreement

from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.web3_internal.web3helper import Web3Helper

logger = logging.getLogger('ocean')


class OceanCompute:
    """Ocean assets class."""

    def __init__(self, ocean_auth, config, data_provider):
        self._auth = ocean_auth
        self._config = config
        self._data_provider = data_provider

    @staticmethod
    def build_cluster_attributes(cluster_type, url):
        """

        :param cluster_type: str (e.g. Kubernetes)
        :param url: str (e.g. http://10.0.0.17/xxx)
        :return:
        """
        return {
            "type": cluster_type,
            "url": url
        }

    @staticmethod
    def build_container_attributes(image, tag, entrypoint):
        """

        :param image: str name of Docker image (e.g. node)
        :param tag: str the Docker image tag (e.g. latest or a specific version number)
        :param entrypoint: str executable file (e.g. node $ALGO)
        :return:
        """
        return {
            "image": image,
            "tag": tag,
            "entrypoint": entrypoint
        }

    @staticmethod
    def build_server_attributes(
            server_id, server_type, cpu, gpu, memory, disk, max_run_time
    ):
        """

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
            "maxExecutionTime": max_run_time
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
                "supportedServers": servers
            }
        }

    @staticmethod
    def create_compute_service_attributes(
            cost, timeout, creator, date_published, provider_attributes):
        """

        :param cost: float the price of this compute service expressed in amount of
            DataTokens. This will be converted to the integer equivalent (Wei) to be stored
            in the DDO service.
        :param timeout: integer maximum amount of running compute service in seconds
        :param creator: str ethereum address
        :param date_published: str timestamp (datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
        :param provider_attributes: dict describing the details of the compute resources (see `build_service_provider_attributes`)
        :return: dict with `main` key and value contain the minimum required attributes of a compute service
        """
        return {
            "main": {
                "name": "dataAssetComputingServiceAgreement",
                "creator": creator,
                "datePublished": date_published,
                "cost": to_base_18(cost),
                "timeout": timeout,
                "provider": provider_attributes
            }
        }

    @staticmethod
    def _status_from_job_info(job_info):
        """
        Helper function to extract the status dict with an added boolean for quick validation
        :param job_info: dict having status and statusText keys
        :return:
        """
        return {
            'ok': job_info['status'] not in (31, 32),
            'status': job_info['status'],
            'statusText': job_info['statusText']
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
            'nodeUri': config.network_url,
            'brizoUri': data_provider.get_url(config),
            'brizoAddress': config.provider_address,
            'metadata': dict(),
            'metadataUri': config.aquarius_url,
            'owner': consumer_address,
            'publishOutput': 0,
            'publishAlgorithmLog': 0,
            'whitelist': [],
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
        compute_endpoint = self._data_provider.get_compute_endpoint(self._config)
        return ServiceDescriptor.compute_service_descriptor(
            attributes=attributes,
            service_endpoint=compute_endpoint
        )

    def _sign_message(self, wallet, msg, nonce=None):
        if nonce is None:
            nonce = self._data_provider.get_nonce(wallet.address, self._config)
        return Web3Helper.sign_hash(
            add_ethereum_prefix_and_hash_msg(f'{msg}{nonce}'),
            wallet
        )

    def start(self, did, consumer_wallet, transfer_tx_id, nonce=None, algorithm_did=None,
              algorithm_meta=None, output=None, job_id=None):
        """Start a remote compute job on the asset files identified by `did` after
        verifying that the provider service is active and transferring the
        number of data-tokens required for using this compute service.

        :param did: str -- id of asset that has the compute service
        :param consumer_wallet: Wallet instance of the consumer ordering the service
        :param transfer_tx_id: hex str -- id of the datatokens transfer transaction
        :param nonce: int value to use in the signature
        :param algorithm_did: str -- the asset did (of `algorithm` type) which consist of `did:op:` and
            the assetId hex str (without `0x` prefix)
        :param algorithm_meta: `AlgorithmMetadata` instance -- metadata about the algorithm being run if
            `algorithm` is being used. This is ignored when `algorithm_did` is specified.
        :param output: dict object to be used in publishing mechanism, must define
        :param job_id: str identifier of a compute job that was previously started and
            stopped (if supported by the provider's  backend)
        :return: str -- id of compute job being executed
        """
        assert algorithm_did or algorithm_meta, 'either an algorithm did or an algorithm meta must be provided.'

        output = OceanCompute.check_output_dict(output, consumer_wallet.address, data_provider=self._data_provider)
        asset = resolve_asset(did, metadata_store_url=self._config.aquarius_url)
        service_endpoint = self._get_service_endpoint(did, asset)

        sa = ServiceAgreement.from_ddo(ServiceTypes.CLOUD_COMPUTE, asset)
        tx_id = transfer_tx_id

        signature = self._sign_message(consumer_wallet, f'{consumer_wallet.address}{did}', nonce=nonce)

        job_info = self._data_provider.start_compute_job(
            did,
            service_endpoint,
            consumer_wallet.address,
            signature,
            sa.index,
            asset.data_token_address,
            tx_id,
            algorithm_did,
            algorithm_meta,
            output,
            job_id
        )
        return job_info['jobId']

    def status(self, did, job_id, wallet):
        """
        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for an existing compute job, keys are (ok, status, statusText)
        """
        msg = f'{wallet.address}{job_id or ""}{did}'
        return OceanCompute._status_from_job_info(
            self._data_provider.compute_job_status(
                did,
                job_id,
                self._get_service_endpoint(did),
                wallet.address,
                self._sign_message(wallet, msg)
            )
        )

    def result(self, did, job_id, wallet):
        """
        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the results/logs urls for an existing compute job, keys are (did, urls, logs)
        """
        msg = f'{wallet.address}{job_id or ""}{did}'
        info_dict = self._data_provider.compute_job_result(
            did,
            job_id,
            self._get_service_endpoint(did),
            wallet.address,
            self._sign_message(wallet, msg)
        )
        return {
            'did': info_dict.get('resultsDid', ''),
            'urls': info_dict.get('resultsUrls', []),
            'logs': info_dict.get('algorithmLogUrl', [])
        }

    def stop(self, did, job_id, wallet):
        """
        Attempt to stop the running compute job

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for the stopped compute job, keys are (ok, status, statusText)
        """
        msg = f'{wallet.address}{job_id or ""}{did}'
        return self._status_from_job_info(
            self._data_provider.stop_compute_job(
                did,
                job_id,
                self._get_service_endpoint(did),
                wallet.address,
                self._sign_message(wallet, msg)
            )
        )

    def restart(self, did, job_id, wallet):
        """
        Attempt to restart the compute job by stopping it first, then starting a new job.

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: str -- id of the new compute job
        """
        msg = f'{wallet.address}{job_id or ""}{did}'
        job_info = self._data_provider.restart_compute_job(
                did,
                job_id,
                self._get_service_endpoint(did),
                wallet.address,
                self._sign_message(wallet, msg)
        )
        return job_info['jobId']

    def _get_service_endpoint(self, did, asset=None):
        if not asset:
            asset = resolve_asset(did, self._config.aquarius_url)

        return ServiceAgreement.from_ddo(ServiceTypes.CLOUD_COMPUTE, asset).service_endpoint

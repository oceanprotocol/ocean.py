#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""Provider module."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import json
import logging
import os
import re
from collections import namedtuple
from json import JSONDecodeError

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.ocean.env_constants import ENV_PROVIDER_API_VERSION
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.web3_internal.web3helper import Web3Helper
from ocean_utils.agreements.service_types import ServiceTypes
from ocean_utils.exceptions import OceanEncryptAssetUrlsError
from ocean_utils.http_requests.requests_session import get_requests_session

logger = logging.getLogger(__name__)

OrderRequirements = namedtuple(
    "OrderRequirements",
    ("amount", "data_token_address", "receiver_address", "nonce", "computeAddress"),
)


class DataServiceProvider:

    """
    The main functions available are:
    - consume_service
    - run_compute_service (not implemented yet)
    """

    _http_client = get_requests_session()
    API_VERSION = "/api/v1"
    provider_info = None

    @staticmethod
    def get_http_client():
        """Get the http client."""
        return DataServiceProvider._http_client

    @staticmethod
    def set_http_client(http_client):
        """Set the http client to something other than the default `requests`."""
        DataServiceProvider._http_client = http_client

    @staticmethod
    def encrypt_files_dict(
        files_dict, encrypt_endpoint, asset_id, publisher_address, signed_did
    ):
        payload = json.dumps(
            {
                "documentId": asset_id,
                "signature": signed_did,
                "document": json.dumps(files_dict),
                "publisherAddress": publisher_address,
            }
        )

        response = DataServiceProvider._http_method(
            "post",
            encrypt_endpoint,
            data=payload,
            headers={"content-type": "application/json"},
        )
        if response and hasattr(response, "status_code"):
            if response.status_code != 201:
                msg = (
                    f"Encrypt file urls failed at the encryptEndpoint "
                    f"{encrypt_endpoint}, reason {response.text}, status {response.status_code}"
                )
                logger.error(msg)
                raise OceanEncryptAssetUrlsError(msg)

            logger.info(
                f"Asset urls encrypted successfully, encrypted urls str: {response.text},"
                f" encryptedEndpoint {encrypt_endpoint}"
            )

            return response.json()["encryptedDocument"]

    @staticmethod
    def sign_message(wallet, msg, config, nonce=None):
        if nonce is None:
            nonce = DataServiceProvider.get_nonce(wallet.address, config)
        print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")
        return Web3Helper.sign_hash(
            add_ethereum_prefix_and_hash_msg(f"{msg}{nonce}"), wallet
        )

    @staticmethod
    def get_nonce(user_address, config):
        _, url = DataServiceProvider.build_endpoint("nonce")
        response = DataServiceProvider._http_method(
            "get", f"{url}?userAddress={user_address}"
        )
        if response.status_code != 200:
            return None

        return response.json()["nonce"]

    @staticmethod
    def get_order_requirements(
        did, service_endpoint, consumer_address, service_id, service_type, token_address
    ):
        """

        :param did:
        :param service_endpoint:
        :param consumer_address: hex str the ethereum account address of the consumer
        :param service_id:
        :param service_type:
        :param token_address:
        :return: OrderRequirements instance -- named tuple (amount, data_token_address, receiver_address, nonce),
        """
        initialize_url = (
            f"{service_endpoint}"
            f"?documentId={did}"
            f"&serviceId={service_id}"
            f"&serviceType={service_type}"
            f"&dataToken={token_address}"
            f"&consumerAddress={consumer_address}"
        )

        logger.info(f"invoke the initialize endpoint with this url: {initialize_url}")
        response = DataServiceProvider._http_method("get", initialize_url)
        # The returned json should contain information about the required number of tokens
        # to consume `service_id`. If service is not available there will be an error or
        # the returned json is empty.
        if response.status_code != 200:
            return None
        order = dict(response.json())

        return OrderRequirements(
            float(order["numTokens"]),
            order["dataToken"],
            order["to"],
            int(order["nonce"]),
            order.get("computeAddress"),
        )

    @staticmethod
    def download_service(
        did,
        service_endpoint,
        wallet,
        files,
        destination_folder,
        service_id,
        token_address,
        order_tx_id,
        index=None,
    ):
        """
        Call the provider endpoint to get access to the different files that form the asset.

        :param did: str id of the asset
        :param service_endpoint: Url to consume, str
        :param wallet: hex str Wallet instance of the consumer signing this request
        :param files: List containing the files to be consumed, list
        :param destination_folder: Path, str
        :param service_id: integer the id of the service inside the DDO's service dict
        :param token_address: hex str the data token address associated with this asset/service
        :param order_tx_id: hex str the transaction hash for the required data token
            transfer (tokens of the same token address above)
        :param index: Index of the document that is going to be downloaded, int
        :return: True if was downloaded, bool
        """
        indexes = range(len(files))
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")
            assert index < len(files), logger.error(
                "index can not be bigger than the number of files"
            )
            indexes = [index]

        base_url = (
            f"{service_endpoint}"
            f"?documentId={did}"
            f"&serviceId={service_id}"
            f"&serviceType={ServiceTypes.ASSET_ACCESS}"
            f"&dataToken={token_address}"
            f"&transferTxId={order_tx_id}"
            f"&consumerAddress={wallet.address}"
        )
        config = ConfigProvider.get_config()
        for i in indexes:
            signature = DataServiceProvider.sign_message(wallet, did, config)
            download_url = base_url + f"&signature={signature}&fileIndex={i}"
            logger.info(f"invoke consume endpoint with this url: {download_url}")
            response = DataServiceProvider._http_method(
                "get", download_url, stream=True
            )
            file_name = DataServiceProvider._get_file_name(response)
            DataServiceProvider.write_file(
                response, destination_folder, file_name or f"file-{i}"
            )

    @staticmethod
    def start_compute_job(
        did: str,
        service_endpoint: str,
        consumer_address: str,
        signature: str,
        service_id: int,
        order_tx_id: str,
        algorithm_did: str = None,
        algorithm_meta: AlgorithmMetadata = None,
        algorithm_tx_id: str = None,
        algorithm_data_token: str = None,
        output: dict = None,
        input_datasets: list = None,
        job_id: str = None,
    ):
        """

        :param did: id of asset starting with `did:op:` and a hex str without 0x prefix
        :param service_endpoint:
        :param consumer_address: hex str the ethereum address of the consumer executing the compute job
        :param signature: hex str signed message to allow the provider to authorize the consumer
        :param service_id:
        :param order_tx_id: hex str id of the token transfer transaction
        :param algorithm_did: str -- the asset did (of `algorithm` type) which consist of `did:op:` and
            the assetId hex str (without `0x` prefix)
        :param algorithm_meta: see `OceanCompute.execute`
        :param algorithm_tx_id: transaction hash of algorithm StartOrder tx (Required when using `algorithm_did`)
        :param algorithm_data_token: datatoken address of this algorithm (Required when using `algorithm_did`)
        :param output: see `OceanCompute.execute`
        :param input_datasets: list of ComputeInput
        :param job_id: str id of compute job that was started and stopped (optional, use it
            here to start a job after it was stopped)

        :return: job_info dict with jobId, status, and other values
        """
        assert (
            algorithm_did or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        payload = DataServiceProvider._prepare_compute_payload(
            did,
            consumer_address,
            service_id,
            order_tx_id,
            signature=signature,
            algorithm_did=algorithm_did,
            algorithm_meta=algorithm_meta,
            algorithm_tx_id=algorithm_tx_id,
            algorithm_data_token=algorithm_data_token,
            output=output,
            input_datasets=input_datasets,
            job_id=job_id,
        )
        logger.info(f"invoke start compute endpoint with this url: {payload}")
        response = DataServiceProvider._http_method(
            "post",
            service_endpoint,
            data=json.dumps(payload),
            headers={"content-type": "application/json"},
        )
        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
        )
        if not response:
            raise AssertionError(
                f"Failed to get a response for request: serviceEndpoint={service_endpoint}, payload={payload}"
            )

        if response.status_code not in (201, 200):
            raise ValueError(response.content.decode("utf-8"))

        try:
            job_info = json.loads(response.content.decode("utf-8"))
            if isinstance(job_info, list):
                return job_info[0]
            return job_info

        except KeyError as err:
            logger.error(f"Failed to extract jobId from response: {err}")
            raise KeyError(f"Failed to extract jobId from response: {err}")
        except JSONDecodeError as err:
            logger.error(f"Failed to parse response json: {err}")
            raise

    @staticmethod
    def stop_compute_job(did, job_id, service_endpoint, consumer_address, signature):
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was stopped successfully
        """
        return DataServiceProvider._send_compute_request(
            "put", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    def restart_compute_job(
        did,
        job_id,
        service_endpoint,
        consumer_address,
        signature,
        service_id,
        order_tx_id,
        algorithm_did=None,
        algorithm_meta=None,
        output=None,
        input_datasets=None,
    ):
        """

        :param did: id of asset starting with `did:op:` and a hex str without 0x prefix
        :param job_id: str id of compute job that was started and stopped (optional, use it
            here to start a job after it was stopped)
        :param service_endpoint:
        :param consumer_address: hex str the ethereum address of the consumer executing the compute job
        :param signature: hex str signed message to allow the provider to authorize the consumer
        :param service_id:
        :param token_address:
        :param order_tx_id: hex str id of the token transfer transaction
        :param algorithm_did: str -- the asset did (of `algorithm` type) which consist of `did:op:` and
            the assetId hex str (without `0x` prefix)
        :param algorithm_meta: see `OceanCompute.execute`
        :param output: see `OceanCompute.execute`
        :param input_datasets: list of ComputeInput

        :return: bool whether the job was restarted successfully
        """
        DataServiceProvider.stop_compute_job(
            did, job_id, service_endpoint, consumer_address, signature
        )
        return DataServiceProvider.start_compute_job(
            did,
            service_endpoint,
            consumer_address,
            signature,
            service_id,
            order_tx_id,
            algorithm_did,
            algorithm_meta,
            output,
            input_datasets=input_datasets,
            job_id=job_id,
        )

    @staticmethod
    def delete_compute_job(did, job_id, service_endpoint, consumer_address, signature):
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was deleted successfully
        """
        return DataServiceProvider._send_compute_request(
            "delete", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    def compute_job_status(did, job_id, service_endpoint, consumer_address, signature):
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to status info. When job_id is not provided, this will return
            status for each job_id that exist for the did
        """
        return DataServiceProvider._send_compute_request(
            "get", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    def compute_job_result(did, job_id, service_endpoint, consumer_address, signature):
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to result urls. When job_id is not provided, this will return
            result for each job_id that exist for the did
        """
        return DataServiceProvider._send_compute_request(
            "get", did, job_id, service_endpoint, consumer_address, signature
        )

    @staticmethod
    def _remove_slash(path):
        if path.endswith("/"):
            path = path[:-1]
        if path.startswith("/"):
            path = path[1:]
        return path

    @staticmethod
    def get_url(config):
        """
        Return the DataProvider component url.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider._remove_slash(
            config.provider_url or "http://localhost:8030"
        )

    @staticmethod
    def get_api_version():
        return DataServiceProvider._remove_slash(
            os.getenv(ENV_PROVIDER_API_VERSION, DataServiceProvider.API_VERSION)
        )

    @staticmethod
    def get_service_endpoints():
        """
        Return the service endpoints from the provider URL.
        """
        if DataServiceProvider.provider_info is None:
            config = ConfigProvider.get_config()
            DataServiceProvider.provider_info = DataServiceProvider._http_method(
                "get", config.provider_url
            ).json()

        return DataServiceProvider.provider_info["serviceEndpoints"]

    @staticmethod
    def get_provider_address(provider_uri=None):
        """
        Return the provider address
        """
        if not provider_uri:
            if DataServiceProvider.provider_info is None:
                config = ConfigProvider.get_config()
                DataServiceProvider.provider_info = DataServiceProvider._http_method(
                    "get", config.provider_url
                ).json()
            return DataServiceProvider.provider_info["providerAddress"]
        provider_info = DataServiceProvider._http_method("get", provider_uri).json()
        return provider_info["providerAddress"]

    @staticmethod
    def build_endpoint(service_name, provider_uri=None, config=None):
        if not provider_uri:
            config = config or ConfigProvider.get_config()
            provider_uri = DataServiceProvider.get_url(config)

        provider_uri = DataServiceProvider._remove_slash(provider_uri)
        parts = provider_uri.split("/")
        if parts[-2] == "services":
            base_url = "/".join(parts[:-2])
            return "GET", urljoin(base_url, "services/initialize")

        api_version = DataServiceProvider.get_api_version()
        if api_version not in provider_uri:
            provider_uri = urljoin(provider_uri, api_version)

        service_endpoints = DataServiceProvider.get_service_endpoints()
        method, url = service_endpoints[service_name]
        url = url.replace(api_version, "")

        return method, urljoin(provider_uri, url)

    @staticmethod
    def build_encrypt_endpoint(provider_uri=None):
        return DataServiceProvider.build_endpoint("encrypt", provider_uri)

    @staticmethod
    def build_initialize_endpoint(provider_uri=None):
        return DataServiceProvider.build_endpoint("initialize", provider_uri)

    @staticmethod
    def build_download_endpoint(provider_uri=None):
        return DataServiceProvider.build_endpoint("download", provider_uri)

    @staticmethod
    def build_compute_endpoint(provider_uri=None):
        return DataServiceProvider.build_endpoint("computeStatus", provider_uri)

    @staticmethod
    def build_stop_compute(provider_uri=None):
        return DataServiceProvider.build_endpoint("computeStop", provider_uri)

    @staticmethod
    def build_start_compute(provider_uri=None):
        return DataServiceProvider.build_endpoint("computeStart", provider_uri)

    @staticmethod
    def build_delete_compute(provider_uri=None):
        return DataServiceProvider.build_endpoint("computeDelete", provider_uri)

    @staticmethod
    def build_fileinfo(provider_uri=None):
        return DataServiceProvider.build_endpoint("fileinfo", provider_uri)

    @staticmethod
    def get_initialize_endpoint(service_endpoint):
        parts = service_endpoint.split("/")
        if parts[-2] == "services":
            base_url = "/".join(parts[:-2])
            return "GET", f"{base_url}/services/initialize"

        return DataServiceProvider.build_initialize_endpoint(service_endpoint)

    @staticmethod
    def get_download_endpoint(config):
        """
        Return the url to consume the asset.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider.build_download_endpoint(
            DataServiceProvider.get_url(config)
        )

    @staticmethod
    def get_compute_endpoint(config):
        """
        Return the url to execute the asset.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider.build_compute_endpoint(
            DataServiceProvider.get_url(config)
        )

    @staticmethod
    def get_encrypt_endpoint(config):
        """
        Return the url to encrypt the asset.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider.build_encrypt_endpoint(
            DataServiceProvider.get_url(config)
        )

    @staticmethod
    def write_file(response, destination_folder, file_name):
        """
        Write the response content in a file in the destination folder.
        :param response: Response
        :param destination_folder: Destination folder, string
        :param file_name: File name, string
        :return: bool
        """
        if response.status_code == 200:
            with open(os.path.join(destination_folder, file_name), "wb") as f:
                for chunk in response.iter_content(chunk_size=None):
                    f.write(chunk)
            logger.info(f"Saved downloaded file in {f.name}")
        else:
            logger.warning(f"consume failed: {response.reason}")

    @staticmethod
    def _send_compute_request(
        http_method, did, job_id, service_endpoint, consumer_address, signature
    ):
        compute_url = (
            f"{service_endpoint}"
            f"?signature={signature}"
            f"&documentId={did}"
            f"&consumerAddress={consumer_address}"
            f'&jobId={job_id or ""}'
        )
        logger.info(f"invoke compute endpoint with this url: {compute_url}")
        response = DataServiceProvider._http_method(http_method, compute_url)
        logger.debug(
            f"got provider execute response: {response.content} with status-code {response.status_code} "
        )
        if response.status_code != 200:
            raise Exception(response.content.decode("utf-8"))

        resp_content = json.loads(response.content.decode("utf-8"))
        if isinstance(resp_content, list):
            return resp_content[0]
        return resp_content

    @staticmethod
    def _get_file_name(response):
        try:
            return re.match(
                r"attachment;filename=(.+)", response.headers.get("content-disposition")
            )[1]
        except Exception as e:
            logger.warning(f"It was not possible to get the file name. {e}")

    @staticmethod
    def _prepare_compute_payload(
        did: str,
        consumer_address: str,
        service_id: int,
        order_tx_id: str,
        signature: str = None,
        algorithm_did: str = None,
        algorithm_meta=None,
        algorithm_tx_id: str = None,
        algorithm_data_token: str = None,
        output: dict = None,
        input_datasets: list = None,
        job_id: str = None,
    ):
        assert (
            algorithm_did or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        if algorithm_meta:
            assert isinstance(algorithm_meta, AlgorithmMetadata), (
                f"expecting a AlgorithmMetadata type "
                f"for `algorithm_meta`, got {type(algorithm_meta)}"
            )
            algorithm_meta = algorithm_meta.as_dictionary()

        _input_datasets = []
        if input_datasets:
            for _input in input_datasets:
                assert _input.did
                assert _input.transfer_tx_id
                assert _input.service_id
                if _input.did != did:
                    _input_datasets.append(_input.as_dictionary())

        payload = {
            "signature": signature,
            "documentId": did,
            "consumerAddress": consumer_address,
            "output": output or dict(),
            "jobId": job_id or "",
            "serviceId": service_id,
            "transferTxId": order_tx_id,
            "additionalInputs": _input_datasets or [],
        }
        if algorithm_did:
            payload.update(
                {
                    "algorithmDid": algorithm_did,
                    "algorithmDataToken": algorithm_data_token,
                    "algorithmTransferTxId": algorithm_tx_id,
                }
            )
        else:
            payload["algorithmMeta"] = algorithm_meta

        return payload

    @staticmethod
    def _http_method(method, *args, **kwargs):
        try:
            return getattr(DataServiceProvider._http_client, method)(*args, **kwargs)
        except Exception:
            logger.error(
                f"Error invoking http method {method}: args={str(args)}, kwargs={str(kwargs)}"
            )
            raise


def urljoin(*args):
    trailing_slash = "/" if args[-1].endswith("/") else ""
    return "/".join(map(lambda x: str(x).strip("/"), args)) + trailing_slash

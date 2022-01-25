#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import json
import logging
import os
import re
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import requests
from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from ocean_lib.config import Config
from ocean_lib.exceptions import DataProviderException, OceanEncryptAssetUrlsError
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.wallet import Wallet
from requests.exceptions import InvalidURL
from requests.models import PreparedRequest, Response
from requests.sessions import Session

logger = logging.getLogger(__name__)


class DataServiceProvider:
    """DataServiceProvider class.

    The main functions available are:
    - consume_service
    - run_compute_service (not implemented yet)
    """

    _http_client = get_requests_session()
    provider_info = None

    @staticmethod
    @enforce_types
    def get_http_client() -> Session:
        """Get the http client."""
        return DataServiceProvider._http_client

    @staticmethod
    @enforce_types
    def set_http_client(http_client: Session) -> None:
        """Set the http client to something other than the default `requests`."""
        DataServiceProvider._http_client = http_client

    @staticmethod
    @enforce_types
    def encrypt(
        objects_to_encrypt: Union[list, str, bytes], encrypt_endpoint: str
    ) -> Response:
        if isinstance(objects_to_encrypt, list):
            data_items = list(map(lambda file: file.to_dict(), objects_to_encrypt))
            data = json.dumps(data_items, separators=(",", ":"))
            payload = data.encode("utf-8")
        elif isinstance(objects_to_encrypt, str):
            payload = objects_to_encrypt.encode("utf-8")
        else:
            payload = objects_to_encrypt

        response = DataServiceProvider._http_method(
            "post",
            encrypt_endpoint,
            data=payload,
            headers={"Content-type": "application/octet-stream"},
        )

        if not response or not hasattr(response, "status_code"):
            raise DataProviderException("Response not found!")

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

        return response

    @staticmethod
    @enforce_types
    def fileinfo(did: str, service_id: str, service_endpoint: str) -> Response:
        payload = {"did": did, "serviceId": service_id}

        response = DataServiceProvider._http_method(
            "post", service_endpoint, json=payload
        )

        if not response or not hasattr(response, "status_code"):
            raise DataProviderException("Response not found!")

        if response.status_code != 200:
            msg = (
                f"Fileinfo service failed at the FileInfoEndpoint "
                f"{service_endpoint}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise DataProviderException(msg)

        logger.info(
            f"Retrieved asset files successfully"
            f" FileInfoEndpoint {service_endpoint}"
        )
        return response

    @staticmethod
    @enforce_types
    def initialize(
        did: str,
        service_id: str,
        consumer_address: str,
        service_endpoint: str,
        compute_environment: Optional[str] = None,
        userdata: Optional[Dict] = None,
        valid_until: Optional[int] = 0,
    ) -> Response:

        req = PreparedRequest()

        # prepare_url function transforms ':' from "did:op:" into "%3".
        service_endpoint += f"?documentId={did}"
        payload = {"serviceId": service_id, "consumerAddress": consumer_address}

        if compute_environment:
            payload["computeEnv"] = compute_environment

        if valid_until:
            payload["validUntil"] = valid_until

        if userdata:
            userdata = json.dumps(userdata)
            payload["userdata"] = userdata

        req.prepare_url(service_endpoint, payload)

        response = DataServiceProvider._http_method("get", req.url)

        if not response or not hasattr(response, "status_code"):
            raise DataProviderException("Response not found!")

        if response.status_code != 200:
            msg = (
                f"Initialize service failed at the initializeEndpoint "
                f"{req.url}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise DataProviderException(msg)

        logger.info(
            f"Service initialized successfully" f" initializeEndpoint {req.url}"
        )

        return response

    @staticmethod
    @enforce_types
    def download(
        did: str,
        service_id: str,
        tx_id: str,
        consumer_wallet: Wallet,
        service_endpoint: str,
        destination_folder: Union[str, Path],
        index: Optional[int] = None,
        userdata: Optional[Dict] = None,
    ) -> None:

        provider_uri = DataServiceProvider.get_root_uri(
            service_endpoint=service_endpoint
        )
        fileinfo_response = DataServiceProvider.fileinfo(
            did, service_id, DataServiceProvider.build_fileinfo(provider_uri)[1]
        )
        files = fileinfo_response.json()
        indexes = range(len(files))
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")
            assert index < len(files), logger.error(
                "index can not be bigger than the number of files"
            )
            indexes = [index]

        req = PreparedRequest()

        # prepare_url function transforms ':' from "did:op:" into "%3".
        service_endpoint += f"?documentId={did}"
        payload = {
            "serviceId": service_id,
            "consumerAddress": consumer_wallet.address,
            "transferTxId": tx_id,
        }

        if userdata:
            userdata = json.dumps(userdata)
            payload["userdata"] = userdata

        for i in indexes:
            payload["fileIndex"] = i
            payload["nonce"], payload["signature"] = DataServiceProvider.sign_message(
                consumer_wallet, did
            )
            req.prepare_url(service_endpoint, payload)
            response = DataServiceProvider._http_method("get", req.url)

            if not response or not hasattr(response, "status_code"):
                raise DataProviderException("Response not found!")

            if response.status_code != 200:
                msg = (
                    f"Download asset failed at the downloadEndpoint "
                    f"{req.url}, reason {response.text}, status {response.status_code}"
                )
                logger.error(msg)
                raise DataProviderException(msg)

            file_name = DataServiceProvider._get_file_name(response)
            DataServiceProvider.write_file(response, destination_folder, file_name)

            logger.info(f"Asset downloaded successfully" f" downloadEndpoint {req.url}")

    @staticmethod
    @enforce_types
    def sign_message(wallet: Wallet, msg: str) -> Tuple[str, str]:
        nonce = str(datetime.now().timestamp())
        print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")
        return nonce, sign_hash(encode_defunct(text=f"{msg}{nonce}"), wallet)

    @staticmethod
    # TODO reinstate @enforce_types
    # @enforce_types
    def start_compute_job(
        service_endpoint: str,
        consumer: Wallet,
        dataset: ComputeInput,
        compute_environment: str,
        algorithm: Optional[ComputeInput] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_custom_data: Optional[str] = None,
        input_datasets: Optional[List[ComputeInput]] = None,
    ) -> Dict[str, Any]:
        """
        Start a compute job.

        Either algorithm or algorithm_meta must be defined.

        :param service_endpoint: str provider compute/start endpoint
        :param consumer: hex str the ethereum address of the consumer executing the compute job
        :param dataset: ComputeInput dataset with a compute service
        :param compute_environment: str compute environment id
        :param algorithm: ComputeInput algorithm witha download service.
        :param algorithm_meta: AlgorithmMetadata algorithm metadata
        :param algorithm_custom_data: TODO
        :param input_datasets: List[ComputeInput] additional input datasets
        :return job_info dict
        """
        assert (
            algorithm or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        payload = DataServiceProvider._prepare_compute_payload(
            consumer=consumer,
            dataset=dataset,
            compute_environment=compute_environment,
            algorithm=algorithm,
            algorithm_meta=algorithm_meta,
            algorithm_custom_data=algorithm_custom_data,
            input_datasets=input_datasets,
        )
        logger.info(f"invoke start compute endpoint with this url: {payload}")
        response = DataServiceProvider._http_method(
            "post",
            service_endpoint,
            data=json.dumps(payload),
            headers={"content-type": "application/json"},
        )
        if response is None:
            raise AssertionError(
                f"Failed to get a response for request: serviceEndpoint={service_endpoint}, payload={payload}, response is {response}"
            )

        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
        )

        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
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
    @enforce_types
    def stop_compute_job(
        did: str, job_id: str, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, Any]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was stopped successfully
        """
        return DataServiceProvider._send_compute_request(
            "put", did, job_id, service_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def delete_compute_job(
        did: str, job_id: str, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, str]:
        """

        :param did: hex str the asset/DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: bool whether the job was deleted successfully
        """
        return DataServiceProvider._send_compute_request(
            "delete", did, job_id, service_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def compute_job_status(
        did: str, job_id: str, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, Any]:
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
            "get", did, job_id, service_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def compute_job_result(
        did: str, job_id: str, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, Any]:
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
            "get", did, job_id, service_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def compute_job_result_file(
        job_id: str, index: int, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, Any]:
        """

        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param index: int compute result index
        :param service_endpoint: str url of the provider service endpoint for compute service
        :param consumer_address: hex str the ethereum address of the consumer's account
        :param signature: hex str signed message to allow the provider to authorize the consumer

        :return: dict of job_id to result urls.
        """
        nonce, signature = DataServiceProvider.sign_message(
            consumer, f"{consumer.address}{job_id}{str(index)}"
        )

        req = PreparedRequest()
        params = {
            "signature": signature,
            "nonce": nonce,
            "jobId": job_id,
            "index": index,
            "consumerAddress": consumer.address,
        }

        req.prepare_url(service_endpoint, params)
        compute_job_result_file_url = req.url

        logger.info(
            f"invoke the computeResult endpoint with this url: {compute_job_result_file_url}"
        )
        response = DataServiceProvider._http_method("get", compute_job_result_file_url)

        if response.status_code != 200:
            raise Exception(response.content)

        return response.content

    @staticmethod
    @enforce_types
    def _remove_slash(path: str) -> str:
        if path.endswith("/"):
            path = path[:-1]
        if path.startswith("/"):
            path = path[1:]
        return path

    @staticmethod
    @enforce_types
    def get_url(config: Config) -> str:
        """
        Return the DataProvider component url.

        :param config: Config
        :return: Url, str
        """
        return DataServiceProvider._remove_slash(config.provider_url)

    @staticmethod
    @enforce_types
    def get_service_endpoints(provider_uri: str) -> Dict[str, List[str]]:
        """
        Return the service endpoints from the provider URL.
        """
        provider_info = DataServiceProvider._http_method("get", provider_uri).json()

        return provider_info["serviceEndpoints"]

    @staticmethod
    @enforce_types
    def get_c2d_address(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProvider._http_method("get", provider_uri).json()

            return provider_info["computeAddress"]
        except requests.exceptions.RequestException:
            pass

        return None

    @staticmethod
    @enforce_types
    def get_provider_address(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProvider._http_method("get", provider_uri).json()

            return provider_info["providerAddress"]
        except requests.exceptions.RequestException:
            pass

        return None

    @staticmethod
    @enforce_types
    def get_root_uri(service_endpoint: str) -> str:
        provider_uri = service_endpoint

        if "/api" in provider_uri:
            i = provider_uri.find("/api")
            provider_uri = provider_uri[:i]

        parts = provider_uri.split("/")

        if len(parts) < 2:
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        if parts[-2] == "services":
            provider_uri = "/".join(parts[:-2])

        result = DataServiceProvider._remove_slash(provider_uri)

        if not result:
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        try:
            root_result = "/".join(parts[0:3])
            response = requests.get(root_result).json()
        except (requests.exceptions.RequestException, JSONDecodeError):
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        if "providerAddress" not in response:
            raise InvalidURL(
                f"Invalid Provider URL {service_endpoint}, no providerAddress."
            )

        return result

    @staticmethod
    @enforce_types
    def is_valid_provider(provider_uri: str) -> bool:
        try:
            DataServiceProvider.get_root_uri(provider_uri)
        except InvalidURL:
            return False

        return True

    @staticmethod
    @enforce_types
    def build_endpoint(service_name: str, provider_uri: str) -> Tuple[str, str]:
        provider_uri = DataServiceProvider.get_root_uri(provider_uri)
        service_endpoints = DataServiceProvider.get_service_endpoints(provider_uri)

        method, url = service_endpoints[service_name]
        return method, urljoin(provider_uri, url)

    @staticmethod
    @enforce_types
    def build_encrypt_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("encrypt", provider_uri)

    @staticmethod
    @enforce_types
    def build_initialize_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("initialize", provider_uri)

    @staticmethod
    @enforce_types
    def build_download_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("download", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("computeStatus", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_result_file_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("computeResult", provider_uri)

    @staticmethod
    @enforce_types
    def build_fileinfo(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProvider.build_endpoint("fileinfo", provider_uri)

    @staticmethod
    @enforce_types
    def write_file(
        response: Response,
        destination_folder: Union[str, bytes, os.PathLike],
        file_name: str,
    ) -> None:
        """
        Write the response content in a file in the destination folder.
        :param response: Response
        :param destination_folder: Destination folder, string
        :param file_name: File name, string
        :return: None
        """
        if response.status_code == 200:
            with open(os.path.join(destination_folder, file_name), "wb") as f:
                for chunk in response.iter_content(chunk_size=None):
                    f.write(chunk)
            logger.info(f"Saved downloaded file in {f.name}")
        else:
            logger.warning(f"consume failed: {response.reason}")

    @staticmethod
    @enforce_types
    def _send_compute_request(
        http_method: str, did: str, job_id: str, service_endpoint: str, consumer: Wallet
    ) -> Dict[str, Any]:
        nonce, signature = DataServiceProvider.sign_message(
            consumer, f"{consumer.address}{job_id}{did}"
        )

        req = PreparedRequest()
        payload = {
            "consumerAddress": consumer.address,
            "documentId": did,
            "jobId": job_id,
            "nonce": nonce,
            "signature": signature,
        }
        req.prepare_url(service_endpoint, payload)

        logger.info(f"invoke compute endpoint with this url: {req.url}")
        response = DataServiceProvider._http_method(http_method, req.url)
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
    @enforce_types
    def _get_file_name(response: Response) -> Optional[str]:
        try:
            return re.match(
                r"attachment;filename=(.+)", response.headers.get("content-disposition")
            )[1]
        except Exception as e:
            logger.warning(f"It was not possible to get the file name. {e}")
            return None

    @staticmethod
    # TODO: reinstate @enforce_types
    # @enforce_types
    def _prepare_compute_payload(
        consumer: Wallet,
        dataset: ComputeInput,
        compute_environment: str,
        algorithm: Optional[ComputeInput] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_custom_data: Optional[str] = None,
        input_datasets: Optional[List[ComputeInput]] = None,
    ) -> Dict[str, Any]:
        assert (
            algorithm or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        if algorithm_meta:
            assert isinstance(algorithm_meta, AlgorithmMetadata), (
                f"expecting a AlgorithmMetadata type "
                f"for `algorithm_meta`, got {type(algorithm_meta)}"
            )

        _input_datasets = []
        if input_datasets:
            for _input in input_datasets:
                assert _input.did, "The received dataset does not have a did."
                assert (
                    _input.transfer_tx_id
                ), "The received dataset does not have a transaction id."
                assert (
                    _input.service_id
                ), "The received dataset does not have a specified service id."
                if _input.did != dataset.did:
                    _input_datasets.append(_input.as_dictionary())

        nonce, signature = DataServiceProvider.sign_message(
            consumer, f"{consumer.address}{dataset.did}"
        )

        payload = {
            "dataset": {
                "documentId": dataset.did,
                "serviceId": dataset.service_id,
                "transferTxId": dataset.transfer_tx_id,
            },
            "computeEnv": compute_environment,
            "algorithm": {},
            "signature": signature,
            "nonce": nonce,
            "consumerAddress": consumer.address,
            "additionalInputs": _input_datasets or [],
        }

        if dataset.userdata:
            payload["dataset"]["userdata"] = dataset.userdata

        if algorithm:
            payload.update(
                {
                    "algorithm": {
                        "documentId": algorithm.did,
                        "serviceId": algorithm.service_id,
                        "transferTxId": algorithm.transfer_tx_id,
                    }
                }
            )
            if algorithm.userdata:
                payload["algorithm"]["userdata"] = algorithm.userdata
            if algorithm_custom_data:
                payload["algorithm"]["algocustomdata"] = algorithm_custom_data
        else:
            payload["algorithm"]["meta"] = algorithm_meta.as_dictionary()

        return payload

    @staticmethod
    @enforce_types
    def _http_method(method: str, *args, **kwargs) -> Optional[Union[Mock, Response]]:
        try:
            return getattr(DataServiceProvider._http_client, method)(*args, **kwargs)
        except Exception:
            logger.error(
                f"Error invoking http method {method}: args={str(args)}, kwargs={str(kwargs)}"
            )
            raise

    @staticmethod
    @enforce_types
    def check_single_file_info(url_object: dict, provider_uri: str) -> bool:
        _, endpoint = DataServiceProvider.build_fileinfo(provider_uri)
        response = requests.post(endpoint, json=url_object)

        if response.status_code != 200:
            return False

        response = response.json()
        for file_info in response:
            return file_info["valid"]

        return False

    @staticmethod
    @enforce_types
    def check_asset_file_info(did: str, service_id: str, provider_uri: str) -> bool:
        if not did:
            return False
        _, endpoint = DataServiceProvider.build_fileinfo(provider_uri)
        data = {"did": did, "serviceId": service_id}
        response = requests.post(endpoint, json=data)

        if response.status_code != 200:
            return False

        response = response.json()
        for ddo_info in response:
            return ddo_info["valid"]

        return False


@enforce_types
def urljoin(*args) -> str:
    trailing_slash = "/" if args[-1].endswith("/") else ""

    return "/".join(map(lambda x: str(x).strip("/"), args)) + trailing_slash

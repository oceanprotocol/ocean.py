#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from enforce_typing import enforce_types
from requests.models import PreparedRequest, Response

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.base import DataServiceProviderBase
from ocean_lib.data_provider.fileinfo_provider import FileInfoProvider
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata

logger = logging.getLogger(__name__)


class DataServiceProvider(DataServiceProviderBase):
    """DataServiceProvider class.

    The main functions available are:
    - consume_service
    - run_compute_service (not implemented yet)
    """

    _http_client = get_requests_session()
    provider_info = None

    @staticmethod
    @enforce_types
    def initialize(
        did: str,
        service: Any,  # Can not add Service typing due to enforce_type errors.
        consumer_address: str,
        userdata: Optional[Dict] = None,
    ) -> Response:
        method, initialize_endpoint = DataServiceProvider.build_endpoint(
            "initialize", service.service_endpoint
        )

        payload = {
            "documentId": did,
            "serviceId": service.id,
            "consumerAddress": consumer_address,
        }

        if userdata is not None:
            userdata = json.dumps(userdata)
            payload["userdata"] = userdata

        response = DataServiceProvider._http_method(
            method, url=initialize_endpoint, params=payload
        )

        DataServiceProviderBase.check_response(
            response, "initializeEndpoint", initialize_endpoint, payload
        )

        logger.info(
            f"Service initialized successfully"
            f" initializeEndpoint {initialize_endpoint}"
        )

        return response

    @staticmethod
    @enforce_types
    def initialize_compute(
        datasets: List[Dict[str, Any]],
        algorithm_data: Dict[str, Any],
        service_endpoint,
        consumer_address: str,
        compute_environment: str,
        valid_until: int,
    ) -> Response:
        """This function initializes compute services.

        To determine the Provider instance that will be called, we rely on the first dataset.
        The first dataset is also required to have a compute service.
        """
        (
            method,
            initialize_compute_endpoint,
        ) = DataServiceProvider.build_endpoint("initializeCompute", service_endpoint)

        payload = {
            "datasets": datasets,
            "algorithm": algorithm_data,
            "compute": {
                "env": compute_environment,
                "validUntil": valid_until,
            },
            "consumerAddress": consumer_address,
        }

        response = DataServiceProvider._http_method(
            method,
            initialize_compute_endpoint,
            data=json.dumps(payload),
            headers={"content-type": "application/json"},
        )

        DataServiceProviderBase.check_response(
            response, "initializeComputeEndpoint", initialize_compute_endpoint, payload
        )

        logger.info(
            f"Service initialized successfully"
            f" initializeComputeEndpoint {initialize_compute_endpoint}"
        )

        return response

    @staticmethod
    @enforce_types
    def download(
        did: str,
        service: Any,  # Can not add Service typing due to enforce_type errors.
        tx_id: Union[str, bytes],
        consumer_wallet,
        destination_folder: Union[str, Path],
        index: Optional[int] = None,
        userdata: Optional[Dict] = None,
    ) -> None:
        service_endpoint = service.service_endpoint
        fileinfo_response = FileInfoProvider.fileinfo(did, service, userdata=userdata)

        files = fileinfo_response.json()
        indexes = range(len(files))
        if index is not None:
            assert isinstance(index, int), logger.error("index has to be an integer.")
            assert index >= 0, logger.error("index has to be 0 or a positive integer.")
            assert index < len(files), logger.error(
                "index can not be bigger than the number of files"
            )
            indexes = [index]

        method, download_endpoint = DataServiceProvider.build_endpoint(
            "download", service_endpoint
        )

        payload = {
            "documentId": did,
            "serviceId": service.id,
            "consumerAddress": consumer_wallet.address,
            "transferTxId": tx_id,
        }

        if userdata:
            userdata = json.dumps(userdata)
            payload["userdata"] = userdata

        for i in indexes:
            payload["fileIndex"] = i
            payload["nonce"], payload["signature"] = DataServiceProvider.sign_message(
                consumer_wallet, did, provider_uri=service_endpoint
            )
            response = DataServiceProvider._http_method(
                method, url=download_endpoint, params=payload, stream=True, timeout=3
            )

            DataServiceProviderBase.check_response(
                response, "downloadEndpoint", download_endpoint, payload
            )

            DataServiceProvider.write_file(response, destination_folder, i)

            logger.info(
                f"DDO downloaded successfully" f" downloadEndpoint {download_endpoint}"
            )

    @staticmethod
    # @enforce_types omitted due to subscripted generics error
    def start_compute_job(
        dataset_compute_service: Any,  # Can not add Service typing due to enforce_type errors.
        consumer,
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

        :param dataset_compute_service:
        :param consumer: hex str the ethereum address of the consumer executing the compute job
        :param dataset: ComputeInput dataset with a compute service
        :param compute_environment: str compute environment id
        :param algorithm: ComputeInput algorithm witha download service.
        :param algorithm_meta: AlgorithmMetadata algorithm metadata
        :param algorithm_custom_data: dict customizable algo parameters (ie. no of iterations, etc)
        :param input_datasets: List[ComputeInput] additional input datasets
        :return job_info dict
        """
        assert (
            algorithm or algorithm_meta
        ), "either an algorithm did or an algorithm meta must be provided."

        assert (
            hasattr(dataset_compute_service, "type")
            and dataset_compute_service.type == ServiceTypes.CLOUD_COMPUTE
        ), "invalid compute service"

        payload = DataServiceProvider._prepare_compute_payload(
            consumer=consumer,
            dataset=dataset,
            compute_environment=compute_environment,
            dataset_compute_service=dataset_compute_service,
            algorithm=algorithm,
            algorithm_meta=algorithm_meta,
            algorithm_custom_data=algorithm_custom_data,
            input_datasets=input_datasets,
        )
        logger.info(f"invoke start compute endpoint with this url: {payload}")
        method, compute_endpoint = DataServiceProvider.build_endpoint(
            "computeStart", dataset_compute_service.service_endpoint
        )
        response = DataServiceProvider._http_method(
            method,
            compute_endpoint,
            data=json.dumps(payload),
            headers={"content-type": "application/json"},
        )

        logger.debug(
            f"got DataProvider execute response: {response.content} with status-code {response.status_code} "
        )

        DataServiceProviderBase.check_response(
            response, "computeStartEndpoint", compute_endpoint, payload, [200, 201]
        )

        try:
            job_info = json.loads(response.content.decode("utf-8"))
            return job_info[0] if isinstance(job_info, list) else job_info

        except KeyError as err:
            logger.error(f"Failed to extract jobId from response: {err}")
            raise KeyError(f"Failed to extract jobId from response: {err}")
        except JSONDecodeError as err:
            logger.error(f"Failed to parse response json: {err}")
            raise

    @staticmethod
    @enforce_types
    def stop_compute_job(
        did: str,
        job_id: str,
        dataset_compute_service: Any,
        consumer,  # Can not add Service typing due to enforce_type errors.
    ) -> Dict[str, Any]:
        """

        :param did: hex str the DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param dataset_compute_service:
        :param consumer of the consumer's account

        :return: bool whether the job was stopped successfully
        """
        _, compute_stop_endpoint = DataServiceProvider.build_endpoint(
            "computeStop", dataset_compute_service.service_endpoint
        )
        return DataServiceProvider._send_compute_request(
            "put", did, job_id, compute_stop_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def delete_compute_job(
        did: str,
        job_id: str,
        dataset_compute_service: Any,
        consumer,  # Can not add Service typing due to enforce_type errors.
    ) -> Dict[str, str]:
        """

        :param did: hex str the DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param dataset_compute_service:
        :param consumer of the consumer's account

        :return: bool whether the job was deleted successfully
        """
        method, compute_delete_endpoint = DataServiceProvider.build_endpoint(
            "computeDelete", dataset_compute_service.service_endpoint
        )
        return DataServiceProvider._send_compute_request(
            method, did, job_id, compute_delete_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def compute_job_status(
        did: str,
        job_id: str,
        dataset_compute_service: Any,
        consumer,  # Can not add Service typing due to enforce_type errors.
    ) -> Dict[str, Any]:
        """

        :param did: hex str the DDO id
        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param dataset_compute_service:
        :param consumer of the consumer's account

        :return: dict of job_id to status info. When job_id is not provided, this will return
            status for each job_id that exist for the did
        """
        method, compute_status_endpoint = DataServiceProvider.build_endpoint(
            "computeStatus", dataset_compute_service.service_endpoint
        )
        return DataServiceProvider._send_compute_request(
            method, did, job_id, compute_status_endpoint, consumer
        )

    @staticmethod
    @enforce_types
    def compute_job_result(
        job_id: str, index: int, dataset_compute_service: Any, consumer
    ) -> bytes:
        """

        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param index: int compute result index
        :param dataset_compute_service:
        :param consumer of the consumer's account

        :return: dict of job_id to result urls.
        """

        nonce, signature = DataServiceProvider.sign_message(
            consumer,
            f"{consumer.address}{job_id}{str(index)}",
            provider_uri=dataset_compute_service.service_endpoint,
        )

        req = PreparedRequest()
        params = {
            "signature": signature,
            "nonce": nonce,
            "jobId": job_id,
            "index": index,
            "consumerAddress": consumer.address,
        }

        (method, compute_job_result_endpoint) = DataServiceProvider.build_endpoint(
            "computeResult", dataset_compute_service.service_endpoint
        )
        req.prepare_url(compute_job_result_endpoint, params)
        compute_job_result_file_url = req.url

        logger.info(
            f"invoke the computeResult endpoint with this url: {compute_job_result_file_url}"
        )
        response = DataServiceProvider._http_method(method, compute_job_result_file_url)

        DataServiceProviderBase.check_response(
            response, "jobResultEndpoint", compute_job_result_endpoint, params
        )

        return response.content

    @staticmethod
    @enforce_types
    def compute_job_result_logs(
        ddo: Any,
        job_id: str,
        dataset_compute_service: Any,
        consumer,
        log_type="output",
    ) -> List[Dict[str, Any]]:
        """

        :param job_id: str id of compute job that was returned from `start_compute_job`
        :param dataset_compute_service:
        :param consumer of the consumer's account

        :return: dict of job_id to result urls.
        """
        status = DataServiceProvider.compute_job_status(
            ddo.did, job_id, dataset_compute_service, consumer
        )
        function_result = []
        for i in range(len(status["results"])):
            result = None
            result_type = status["results"][i]["type"]
            result = DataServiceProvider.compute_job_result(
                job_id, i, dataset_compute_service, consumer
            )

            # Extract algorithm output
            if result_type == log_type:
                function_result.append(result)

        return function_result

    @staticmethod
    @enforce_types
    def _send_compute_request(
        http_method: str, did: str, job_id: str, service_endpoint: str, consumer
    ) -> Dict[str, Any]:
        nonce, signature = DataServiceProvider.sign_message(
            consumer,
            f"{consumer.address}{job_id}{did}",
            provider_uri=service_endpoint,
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

        DataServiceProviderBase.check_response(
            response, "compute Endpoint", req.url, payload
        )

        resp_content = json.loads(response.content.decode("utf-8"))

        if isinstance(resp_content, list):
            return resp_content[0]

        return resp_content

    @staticmethod
    # @enforce_types omitted due to subscripted generics error
    def _prepare_compute_payload(
        consumer,
        dataset: ComputeInput,
        dataset_compute_service: Any,  # Can not add Service typing due to enforce_type errors.
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

        input_datasets = input_datasets if input_datasets else []
        _input_datasets = []
        for _input in input_datasets:
            for req_key in ["did", "transfer_tx_id", "service_id"]:
                assert getattr(
                    _input, req_key
                ), f"The received dataset does not have a {req_key}."

        # TODO: is the nonce correct here?
        # Should it be the one from the compute service or a dataset?
        nonce, signature = DataServiceProvider.sign_message(
            consumer,
            f"{consumer.address}{dataset.did}",
            provider_uri=dataset_compute_service.service_endpoint,
        )

        payload = {
            "dataset": {
                "documentId": dataset.did,
                "serviceId": dataset.service_id,
                "transferTxId": dataset.transfer_tx_id,
            },
            "environment": compute_environment,
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
            payload["algorithm"] = algorithm_meta.as_dictionary()

        return payload

    @staticmethod
    @enforce_types
    def check_single_file_info(url_object: dict, provider_uri: str) -> bool:
        method, endpoint = DataServiceProvider.build_endpoint("fileinfo", provider_uri)
        response = DataServiceProvider._http_method(method, endpoint, json=url_object)

        if response.status_code != 200:
            return False

        return any([file_info["valid"] for file_info in response.json()])

    @staticmethod
    @enforce_types
    def check_asset_file_info(
        did: str, service_id: str, provider_uri: str, userdata: Optional[dict] = None
    ) -> bool:
        if not did:
            return False

        method, endpoint = DataServiceProvider.build_endpoint("fileinfo", provider_uri)
        data = {"did": did, "serviceId": service_id}

        if userdata is not None:
            data["userdata"] = userdata

        response = DataServiceProvider._http_method(method, endpoint, json=data)

        if not response or response.status_code != 200:
            return False

        return any([file_info["valid"] for file_info in response.json()])

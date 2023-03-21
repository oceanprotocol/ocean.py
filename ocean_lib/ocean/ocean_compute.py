#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Dict, List, Optional, Type

from enforce_typing import enforce_types

from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.aquarius import Aquarius
from ocean_lib.assets.asset_downloader import is_consumable
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata

logger = logging.getLogger("ocean")


class OceanCompute:
    @enforce_types
    def __init__(
        self, config_dict: dict, data_provider: Type[DataServiceProvider]
    ) -> None:
        """Initialises OceanCompute class."""
        self._config_dict = config_dict
        self._data_provider = data_provider

    @enforce_types
    def start(
        self,
        consumer_wallet,
        dataset: ComputeInput,
        compute_environment: str,
        algorithm: Optional[ComputeInput] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_algocustomdata: Optional[dict] = None,
        additional_datasets: List[ComputeInput] = [],
    ) -> str:
        metadata_cache_uri = self._config_dict.get("METADATA_CACHE_URI")
        ddo = Aquarius.get_instance(metadata_cache_uri).get_ddo(dataset.did)
        service = ddo.get_service_by_id(dataset.service_id)
        assert (
            ServiceTypes.CLOUD_COMPUTE == service.type
        ), "service at serviceId is not of type compute service."

        consumable_result = is_consumable(
            ddo,
            service,
            {"type": "address", "value": consumer_wallet.address},
            with_connectivity_check=True,
        )
        if consumable_result != ConsumableCodes.OK:
            raise AssetNotConsumable(consumable_result)

        # Start compute job
        job_info = self._data_provider.start_compute_job(
            dataset_compute_service=service,
            consumer=consumer_wallet,
            dataset=dataset,
            compute_environment=compute_environment,
            algorithm=algorithm,
            algorithm_meta=algorithm_meta,
            algorithm_custom_data=algorithm_algocustomdata,
            input_datasets=additional_datasets,
        )
        return job_info["jobId"]

    @enforce_types
    def status(self, ddo: DDO, service: Service, job_id: str, wallet) -> Dict[str, Any]:
        """
        Gets job status.

        :param ddo: DDO offering the compute service of this job
        :param service: compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for an existing compute job, keys are (ok, status, statusText)
        """
        job_info = self._data_provider.compute_job_status(
            ddo.did, job_id, service, wallet
        )
        job_info.update({"ok": job_info.get("status") not in (31, 32, None)})

        return job_info

    @enforce_types
    def result(
        self, ddo: DDO, service: Service, job_id: str, index: int, wallet
    ) -> Dict[str, Any]:
        """
        Gets job result.

        :param ddo: DDO offering the compute service of this job
        :param service: compute service of this job
        :param job_id: str id of the compute job
        :param index: compute result index
        :param wallet: Wallet instance
        :return: dict the results/logs urls for an existing compute job, keys are (did, urls, logs)
        """
        result = self._data_provider.compute_job_result(job_id, index, service, wallet)

        return result

    @enforce_types
    def compute_job_result_logs(
        self,
        ddo: DDO,
        service: Service,
        job_id: str,
        wallet,
        log_type="output",
    ) -> Dict[str, Any]:
        """
        Gets job output if exists.

        :param ddo: DDO offering the compute service of this job
        :param service: compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the results/logs urls for an existing compute job, keys are (did, urls, logs)
        """
        result = self._data_provider.compute_job_result_logs(
            ddo, job_id, service, wallet, log_type
        )

        return result

    @enforce_types
    def stop(self, ddo: DDO, service: Service, job_id: str, wallet) -> Dict[str, Any]:
        """
        Attempt to stop the running compute job.

        :param ddo: DDO offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for the stopped compute job, keys are (ok, status, statusText)
        """
        job_info = self._data_provider.stop_compute_job(
            ddo.did, job_id, service, wallet
        )
        job_info.update({"ok": job_info.get("status") not in (31, 32, None)})
        return job_info

    @enforce_types
    def get_c2d_environments(self, service_endpoint: str, chain_id: int) -> str:
        return DataServiceProvider.get_c2d_environments(service_endpoint, chain_id)

    @enforce_types
    def get_free_c2d_environment(self, service_endpoint: str, chain_id) -> str:
        environments = self.get_c2d_environments(service_endpoint, chain_id)
        return next(env for env in environments if float(env["priceMin"]) == float(0))

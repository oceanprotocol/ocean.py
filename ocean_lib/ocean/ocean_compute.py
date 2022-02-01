#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from enforce_typing import enforce_types

from ocean_lib.agreements.consumable import AssetNotConsumable, ConsumableCodes
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.assets.asset_resolver import resolve_asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.algorithm_metadata import AlgorithmMetadata
from ocean_lib.models.compute_input import ComputeInput
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

    @enforce_types
    def start(
        self,
        consumer_wallet: Wallet,
        dataset: ComputeInput,
        compute_environment: str,
        algorithm: Optional[ComputeInput] = None,
        algorithm_meta: Optional[AlgorithmMetadata] = None,
        algorithm_algocustomdata: Optional[dict] = None,
        additional_datasets: List[ComputeInput] = [],
    ) -> str:
        asset = resolve_asset(
            dataset.did, metadata_cache_uri=self._config.metadata_cache_uri
        )
        service = asset.get_service_by_id(dataset.service_id)
        assert (
            ServiceTypes.CLOUD_COMPUTE == service.type
        ), "service at serviceId is not of type compute service."

        consumable_result = service.is_consumable(
            asset,
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
    def status(self, did: str, job_id: str, wallet: Wallet) -> Dict[str, Any]:
        """
        Gets job status.

        :param did: str id of the asset offering the compute service of this job
        :param job_id: str id of the compute job
        :param wallet: Wallet instance
        :return: dict the status for an existing compute job, keys are (ok, status, statusText)
        """
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        dataset_compute_service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)

        return OceanCompute._status_from_job_info(
            self._data_provider.compute_job_status(
                did, job_id, dataset_compute_service, wallet
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
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        dataset_compute_service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)

        info_dict = self._data_provider.compute_job_result(
            did, job_id, dataset_compute_service, wallet
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
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        dataset_compute_service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)

        result = self._data_provider.compute_job_result_file(
            job_id, index, dataset_compute_service, wallet
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
        asset = resolve_asset(did, metadata_cache_uri=self._config.metadata_cache_uri)
        dataset_compute_service = asset.get_service(ServiceTypes.CLOUD_COMPUTE)

        return self._status_from_job_info(
            self._data_provider.stop_compute_job(
                did, job_id, dataset_compute_service, wallet
            )
        )

    @enforce_types
    def _get_service_endpoint(
        self, did: str, asset: Optional[Asset] = None
    ) -> Tuple[str, str]:
        if not asset:
            asset = resolve_asset(did, self._config.metadata_cache_uri)

        return self._data_provider.build_compute_endpoint(
            asset.get_service(ServiceTypes.CLOUD_COMPUTE).service_endpoint
        )

    @enforce_types
    def _get_compute_result_file_endpoint(
        self, did: str, asset: Optional[Asset] = None
    ) -> Tuple[str, str]:
        if not asset:
            asset = resolve_asset(did, self._config.metadata_cache_uri)

        return self._data_provider.build_compute_result_file_endpoint(
            asset.get_service(ServiceTypes.CLOUD_COMPUTE).service_endpoint
        )

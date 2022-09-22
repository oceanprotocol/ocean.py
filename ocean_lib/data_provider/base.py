#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import logging
import os
import re
from datetime import datetime
from json import JSONDecodeError
from typing import Any, Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import requests
from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from requests.exceptions import InvalidURL
from requests.models import Response
from requests.sessions import Session
from web3.main import Web3

from ocean_lib.exceptions import DataProviderException
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.web3_internal.transactions import sign_hash
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)
keys = KeyAPI(NativeECCBackend)


class DataServiceProviderBase:
    """DataServiceProviderBase class."""

    _http_client = get_requests_session()
    provider_info = None

    @staticmethod
    @enforce_types
    def get_http_client() -> Session:
        """Get the http client."""
        return DataServiceProviderBase._http_client

    @staticmethod
    @enforce_types
    def set_http_client(http_client: Session) -> None:
        """Set the http client to something other than the default `requests`."""
        DataServiceProviderBase._http_client = http_client

    @staticmethod
    @enforce_types
    def sign_message(wallet: Wallet, msg: str) -> Tuple[str, str]:
        nonce = str(datetime.utcnow().timestamp())
        print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")
        message_hash = Web3.solidityKeccak(
            ["bytes"],
            [Web3.toBytes(text=f"{msg}{nonce}")],
        )
        return nonce, sign_hash(encode_defunct(message_hash), wallet)

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
    def get_url(config_dict: dict) -> str:
        """
        Return the DataProvider component url.

        :return: Url, str
        """
        return DataServiceProviderBase._remove_slash(config_dict.get("PROVIDER_URL"))

    @staticmethod
    @enforce_types
    def get_service_endpoints(provider_uri: str) -> Dict[str, List[str]]:
        """
        Return the service endpoints from the provider URL.
        """
        provider_info = DataServiceProviderBase._http_method(
            "get", url=provider_uri
        ).json()

        return provider_info["serviceEndpoints"]

    @staticmethod
    @enforce_types
    def get_c2d_environments(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            _, envs_endpoint = DataServiceProviderBase.build_c2d_environments_endpoint(
                provider_uri
            )
            environments = DataServiceProviderBase._http_method(
                "get", envs_endpoint
            ).json()

            return environments
        except requests.exceptions.RequestException:
            pass

        return []

    @staticmethod
    @enforce_types
    def get_provider_address(provider_uri: str) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProviderBase._http_method(
                "get", provider_uri
            ).json()

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

        result = DataServiceProviderBase._remove_slash(provider_uri)

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
            DataServiceProviderBase.get_root_uri(provider_uri)
        except InvalidURL:
            return False

        return True

    @staticmethod
    @enforce_types
    def build_endpoint(service_name: str, provider_uri: str) -> Tuple[str, str]:
        provider_uri = DataServiceProviderBase.get_root_uri(provider_uri)
        service_endpoints = DataServiceProviderBase.get_service_endpoints(provider_uri)

        method, url = service_endpoints[service_name]
        return method, urljoin(provider_uri, url)

    @staticmethod
    @enforce_types
    def build_encrypt_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("encrypt", provider_uri)

    @staticmethod
    @enforce_types
    def build_initialize_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("initialize", provider_uri)

    @staticmethod
    @enforce_types
    def build_initialize_compute_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("initializeCompute", provider_uri)

    @staticmethod
    @enforce_types
    def build_download_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("download", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("computeStatus", provider_uri)

    @staticmethod
    @enforce_types
    def build_compute_result_file_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("computeResult", provider_uri)

    @staticmethod
    @enforce_types
    def build_fileinfo(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint("fileinfo", provider_uri)

    @staticmethod
    @enforce_types
    def build_c2d_environments_endpoint(provider_uri: str) -> Tuple[str, str]:
        return DataServiceProviderBase.build_endpoint(
            "computeEnvironments", provider_uri
        )

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
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)
            logger.info(f"Saved downloaded file in {f.name}")
        else:
            logger.warning(f"consume failed: {response.reason}")

    @staticmethod
    @enforce_types
    def _validate_content_disposition(header: str) -> bool:
        pattern = re.compile(r"\\|\.\.|/")
        return not bool(pattern.findall(header))

    @staticmethod
    @enforce_types
    def _get_file_name(response: Response) -> Optional[str]:
        try:
            if not DataServiceProviderBase._validate_content_disposition(
                response.headers.get("content-disposition")
            ):
                logger.error(
                    "Invalid content disposition format. It was not possible to get the file name."
                )
                return None
            return re.match(
                r"attachment;filename=(.+)",
                response.headers.get("content-disposition"),
            )[1]
        except Exception as e:
            logger.warning(f"It was not possible to get the file name. {e}")
            return None

    @staticmethod
    @enforce_types
    def _http_method(method: str, *args, **kwargs) -> Optional[Union[Mock, Response]]:
        try:
            return getattr(DataServiceProviderBase._http_client, method)(
                *args, **kwargs
            )
        except Exception:
            logger.error(
                f"Error invoking http method {method}: args={str(args)}, kwargs={str(kwargs)}"
            )
            raise

    @staticmethod
    @enforce_types
    def check_response(
        response: Any,
        endpoint_name: str,
        endpoint: str,
        payload: Union[Dict, bytes],
        success_codes: Optional[List] = None,
        exception_type=DataProviderException,
    ):
        if not response or not hasattr(response, "status_code"):
            if isinstance(response, Response) and response.status_code == 400:
                error = response.json().get("error", None)
                if error is None:
                    error = response.json().get("errors", "unknown error")

                raise DataProviderException(f"{endpoint_name} failed: {error}")

            raise DataProviderException(
                f"Failed to get a response for request: {endpoint_name}={endpoint}, payload={payload}, response is {response}"
            )

        if not success_codes:
            success_codes = [200]

        if response.status_code not in success_codes:
            msg = (
                f"request failed at the {endpoint_name}"
                f"{endpoint}, reason {response.text}, status {response.status_code}"
            )
            logger.error(msg)
            raise exception_type(msg)

        return None


@enforce_types
def urljoin(*args) -> str:
    trailing_slash = "/" if args[-1].endswith("/") else ""

    return "/".join(map(lambda x: str(x).strip("/"), args)) + trailing_slash

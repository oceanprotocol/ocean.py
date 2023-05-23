#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Provider module."""
import logging
import os
import re
from datetime import datetime, timezone
from json import JSONDecodeError
from typing import Dict, List, Optional, Tuple, Union
from unittest.mock import Mock

import requests
from brownie.network.account import ClefAccount
from enforce_typing import enforce_types
from requests.exceptions import InvalidURL
from requests.models import PreparedRequest, Response
from requests.sessions import Session

from ocean_lib.exceptions import DataProviderException
from ocean_lib.http_requests.requests_session import get_requests_session
from ocean_lib.web3_internal.utils import sign_with_clef, sign_with_key

logger = logging.getLogger(__name__)


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
    def sign_message(wallet, msg: str) -> Tuple[str, str]:
        nonce = str(datetime.now(timezone.utc).timestamp() * 1000)
        print(f"signing message with nonce {nonce}: {msg}, account={wallet.address}")

        if isinstance(wallet, ClefAccount):
            return nonce, str(sign_with_clef(f"{msg}{nonce}", wallet))

        return nonce, str(sign_with_key(f"{msg}{nonce}", wallet.private_key))

    @staticmethod
    @enforce_types
    def get_url(config_dict: dict) -> str:
        """
        Return the DataProvider component url.

        :return: Url, str
        """
        return _remove_slash(config_dict.get("PROVIDER_URL"))

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
    def get_c2d_environments(provider_uri: str, chain_id: int) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            method, envs_endpoint = DataServiceProviderBase.build_endpoint(
                "computeEnvironments", provider_uri, {"chainId": chain_id}
            )
            environments = DataServiceProviderBase._http_method(
                method, url=envs_endpoint
            ).json()

            if str(chain_id) not in environments:
                logger.warning(
                    "You might be using an older provider. ocean.py can not verify the chain id."
                )
                return environments

            return environments[str(chain_id)]
        except (requests.exceptions.RequestException, KeyError):
            pass

        return []

    @staticmethod
    @enforce_types
    def get_provider_address(provider_uri: str, chain_id: int) -> Optional[str]:
        """
        Return the provider address
        """
        try:
            provider_info = DataServiceProviderBase._http_method(
                "get", provider_uri
            ).json()

            if "providerAddress" in provider_info:
                logger.warning(
                    "You might be using an older provider. ocean.py can not verify the chain id."
                )
                return provider_info["providerAddress"]

            return provider_info["providerAddresses"][str(chain_id)]
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

        result = _remove_slash(provider_uri)

        if not result:
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        try:
            root_result = "/".join(parts[0:3])
            response = requests.get(root_result).json()
        except (requests.exceptions.RequestException, JSONDecodeError):
            raise InvalidURL(f"InvalidURL {service_endpoint}.")

        if "providerAddresses" not in response:
            if "providerAddress" in response:
                logger.warning(
                    "You might be using an older provider. ocean.py can not verify the chain id."
                )
            else:
                raise InvalidURL(
                    f"Invalid Provider URL {service_endpoint}, no providerAddresses."
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
    def build_endpoint(
        service_name: str, provider_uri: str, params: Optional[dict] = None
    ) -> Tuple[str, str]:
        provider_uri = DataServiceProviderBase.get_root_uri(provider_uri)
        service_endpoints = DataServiceProviderBase.get_service_endpoints(provider_uri)

        method, url = service_endpoints[service_name]
        url = urljoin(provider_uri, url)

        if params:
            req = PreparedRequest()
            req.prepare_url(url, params)
            url = req.url

        return method, url

    @staticmethod
    @enforce_types
    def write_file(
        response: Response,
        destination_folder: Union[str, bytes, os.PathLike],
        index: int,
    ) -> None:
        """
        Write the response content in a file in the destination folder.
        :param response: Response
        :param destination_folder: Destination folder, string
        :param index: file index
        :return: None
        """
        if response.status_code != 200:
            logger.warning(f"consume failed: {response.reason}")
            return

        with open(os.path.join(destination_folder, f"file{index}"), "wb") as f:
            for chunk in response.iter_content(chunk_size=4096):
                f.write(chunk)
        logger.info(f"Saved downloaded file in {f.name}")

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
            return getattr(DataServiceProviderBase._http_client, method.lower())(
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
        response,
        endpoint_name: str,
        endpoint: str,
        payload: Union[Dict, bytes],
        success_codes: Optional[List] = None,
        exception_type=DataProviderException,
    ):
        if not response or not hasattr(response, "status_code"):
            if isinstance(response, Response) and response.status_code == 400:
                error = response.json().get(
                    "error", response.json().get("errors", "unknown error")
                )

                raise DataProviderException(f"{endpoint_name} failed: {error}")

            response_content = getattr(response, "content", "<none>")

            raise DataProviderException(
                f"Failed to get a response for request: {endpoint_name}={endpoint}, payload={payload}, response is {response_content}"
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


def _remove_slash(path: str) -> str:
    path = path[:-1] if path.endswith("/") else path
    path = path[1:] if path.startswith("/") else path

    return path

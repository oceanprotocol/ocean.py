from ocean_lib.config_provider import ConfigProvider

from ocean_lib.data_provider.data_service_provider import (
    DataServiceProvider as DSP,
    urljoin,
)
from tests.resources.helper_functions import get_publisher_ocean_instance


TEST_SERVICE_ENDPOINTS = {
    "computeDelete": ["DELETE", "/api/v1/services/compute"],
    "computeStart": ["POST", "/api/v1/services/compute"],
    "computeStatus": ["GET", "/api/v1/services/compute"],
    "computeStop": ["PUT", "/api/v1/services/compute"],
    "download": ["GET", "/api/v1/services/download"],
    "encrypt": ["POST", "/api/v1/services/encrypt"],
    "fileinfo": ["POST", "/api/v1/services/fileinfo"],
    "initialize": ["GET", "/api/v1/services/initialize"],
    "nonce": ["GET", "/api/v1/services/nonce"],
}


def test_expose_endpoints():
    service_endpoints = TEST_SERVICE_ENDPOINTS
    valid_endpoints = DSP.get_service_endpoints()
    assert len(valid_endpoints) == len(service_endpoints)
    assert [
        valid_endpoints[key] for key in set(service_endpoints) & set(valid_endpoints)
    ]


def test_provider_address():
    provider_address = DSP.get_provider_address()
    assert provider_address, "Failed to get provider address."


def test_provider_address_with_url():
    p_ocean_instance = get_publisher_ocean_instance()
    provider_address = DSP.get_provider_address(DSP.get_url(p_ocean_instance.config))
    assert provider_address, "Failed to get provider address."


def test_get_root_uri():
    uri = "http://ppp.com"
    assert DSP.get_root_uri(uri) == uri
    assert DSP.get_root_uri("http://ppp.com:8000") == "http://ppp.com:8000"
    assert (
        DSP.get_root_uri("http://ppp.com:8000/api/v1/services/")
        == "http://ppp.com:8000"
    )
    assert DSP.get_root_uri("http://ppp.com:8000/api/v1") == "http://ppp.com:8000"
    assert (
        DSP.get_root_uri("http://ppp.com:8000/services")
        == "http://ppp.com:8000/services"
    )
    assert (
        DSP.get_root_uri("http://ppp.com:8000/services/download")
        == "http://ppp.com:8000"
    )
    assert (
        DSP.get_root_uri("http://ppp.com:8000/api/v2/services")
        == "http://ppp.com:8000/api/v2/services"
    )
    assert (
        DSP.get_root_uri("http://ppp.com:8000/api/v2/services/")
        == "http://ppp.com:8000/api/v2"
    )


def test_build_endpoint():
    def get_service_endpoints(_provider_uri=None):
        _endpoints = TEST_SERVICE_ENDPOINTS.copy()
        _endpoints.update({"newEndpoint": ["GET", "/api/v1/services/newthing"]})
        return _endpoints

    original_func = DSP.get_service_endpoints
    DSP.get_service_endpoints = get_service_endpoints
    config = ConfigProvider.get_config()

    endpoints = get_service_endpoints()
    uri = "http://ppp.com"
    method, endpnt = DSP.build_endpoint("newEndpoint", provider_uri=uri)
    assert endpnt == urljoin(uri, endpoints["newEndpoint"][1])
    # config has no effect when provider_uri is set
    assert (
        endpnt == DSP.build_endpoint("newEndpoint", provider_uri=uri, config=config)[1]
    )

    method, endpnt = DSP.build_endpoint("newEndpoint", config=config)
    assert endpnt == urljoin(
        DSP.get_root_uri(config.provider_url), endpoints["newEndpoint"][1]
    )
    assert (
        endpnt == DSP.build_endpoint("newEndpoint", provider_uri=config.provider_url)[1]
    )

    uri = "http://ppp.com:8030/api/v1/services/newthing"
    method, endpnt = DSP.build_endpoint("download", provider_uri=uri)
    assert method == endpoints["download"][0]
    assert endpnt == urljoin(DSP.get_root_uri(uri), endpoints["download"][1])

    DSP.get_service_endpoints = original_func


def test_build_specific_endpoints():
    config = ConfigProvider.get_config()
    endpoints = TEST_SERVICE_ENDPOINTS

    def get_service_endpoints(_provider_uri=None):
        return TEST_SERVICE_ENDPOINTS.copy()

    original_func = DSP.get_service_endpoints
    DSP.get_service_endpoints = get_service_endpoints

    base_uri = DSP.get_root_uri(config.provider_url)
    assert DSP.build_download_endpoint()[1] == urljoin(
        base_uri, endpoints["download"][1]
    )
    assert DSP.build_initialize_endpoint()[1] == urljoin(
        base_uri, endpoints["initialize"][1]
    )
    assert DSP.build_encrypt_endpoint()[1] == urljoin(base_uri, endpoints["encrypt"][1])
    assert DSP.build_fileinfo()[1] == urljoin(base_uri, endpoints["fileinfo"][1])
    assert DSP.build_compute_endpoint()[1] == urljoin(
        base_uri, endpoints["computeStatus"][1]
    )
    assert DSP.build_compute_endpoint()[1] == urljoin(
        base_uri, endpoints["computeStart"][1]
    )
    assert DSP.build_compute_endpoint()[1] == urljoin(
        base_uri, endpoints["computeStop"][1]
    )
    assert DSP.build_compute_endpoint()[1] == urljoin(
        base_uri, endpoints["computeDelete"][1]
    )

    DSP.get_service_endpoints = original_func

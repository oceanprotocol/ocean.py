#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.agreements.service_types import ServiceTypes


def enable_flag(ddo, flag_name):
    metadata_service = ddo.get_service(ServiceTypes.METADATA)

    if not metadata_service:
        return

    if "status" not in metadata_service.attributes:
        metadata_service.attributes["status"] = {}

    if flag_name == "isListed":  # only one that defaults to True
        metadata_service.attributes["status"].pop(flag_name)
    else:
        metadata_service.attributes["status"][flag_name] = True


def disable_flag(ddo, flag_name):
    metadata_service = ddo.get_service(ServiceTypes.METADATA)

    if not metadata_service:
        return

    if "status" not in metadata_service.attributes:
        metadata_service.attributes["status"] = {}

    if flag_name == "isListed":  # only one that defaults to True
        metadata_service.attributes["status"][flag_name] = False
    else:
        metadata_service.attributes["status"].pop(flag_name)


def is_flag_enabled(ddo, flag_name):
    metadata_service = ddo.get_service(ServiceTypes.METADATA)
    default = flag_name == "isListed"  # only one that defaults to True

    if not metadata_service or "status" not in metadata_service.attributes:
        return default

    return metadata_service.attributes["status"].get(flag_name, default)

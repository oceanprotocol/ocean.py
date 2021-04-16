#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from eth_utils import add_0x_prefix, remove_0x_prefix
from web3 import Web3


class Parameter:
    """
    Parameter of the condition.
    Form by a parameter name, a type and a value.
    """

    def __init__(self, param_json):
        self.name = param_json["name"]
        self.type = param_json["type"]
        self.value = param_json["value"]
        if self.type == "bytes32":
            self.value = add_0x_prefix(self.value)

    def as_dictionary(self):
        """
        Return the parameter as a dictionary.

        :return: dict
        """
        return {
            "name": self.name,
            "type": self.type,
            "value": remove_0x_prefix(self.value)
            if self.type == "bytes32"
            else self.value,
        }


class Event:
    """
    Example: (formatted to make Sphinx happy!)

    {
    "name": "PaymentLocked",
    "actorType": ["publisher"],
    "handlers": {
    "moduleName": "accessControl",
    "functionName": "grantAccess",
    "version": "0.1"
    }
    }
    """

    def __init__(self, event_json):
        self.values_dict = dict(event_json)

    @property
    def name(self):
        return self.values_dict["name"]

    @property
    def actor_type(self):
        return self.values_dict["actorType"]

    @property
    def handler_module_name(self):
        return self.values_dict["handler"]["moduleName"]

    @property
    def handler_function_name(self):
        return self.values_dict["handler"]["functionName"]

    @property
    def handler_version(self):
        return self.values_dict["handler"]["version"]

    def as_dictionary(self):
        return self.values_dict


class ServiceAgreementCondition(object):
    """Class representing the Service Agreement Conditions."""

    def __init__(self, condition_json=None):
        self.name = ""
        self.timelock = 0
        self.timeout = 0
        self.contract_name = ""
        self.function_name = ""
        self.is_terminal = False
        self.dependencies = []
        self.timeout_flags = []
        self.parameters = []
        self.events = []
        if condition_json:
            self.init_from_condition_json(condition_json)

    def init_from_condition_json(self, condition_json):
        """
        Init the condition values from a condition json.

        :param condition_json: dict
        """
        self.name = condition_json["name"]
        self.timelock = condition_json["timelock"]
        self.timeout = condition_json["timeout"]
        self.contract_name = condition_json["contractName"]
        self.function_name = condition_json["functionName"]
        self.parameters = [Parameter(p) for p in condition_json["parameters"]]
        self.events = [Event(e) for e in condition_json["events"]]

    def as_dictionary(self):
        """
        Return the condition as a dictionary.

        :return: dict
        """
        condition_dict = {
            "name": self.name,
            "timelock": self.timelock,
            "timeout": self.timeout,
            "contractName": self.contract_name,
            "functionName": self.function_name,
            "events": [e.as_dictionary() for e in self.events],
            "parameters": [p.as_dictionary() for p in self.parameters],
        }

        return condition_dict

    @property
    def param_types(self):
        """
        Type of the conditions.

        :return: list of types.
        """
        return [parameter.type for parameter in self.parameters]

    @property
    def param_values(self):
        """
        Values of the conditions.

        :return: list of values.
        """
        return [parameter.value for parameter in self.parameters]

    @property
    def values_hash(self):
        """
        Value hashes

        :return:
        """
        return Web3.soliditySha3(self.param_types, self.param_values).hex()

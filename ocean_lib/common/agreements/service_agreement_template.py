#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy

from ocean_lib.common.agreements.service_agreement_condition import (
    Event,
    ServiceAgreementCondition,
)


class ServiceAgreementTemplate(object):
    """Class representing a Service Agreement Template."""

    TEMPLATE_ID_KEY = "templateId"

    def __init__(self, template_id=None, name=None, creator=None, template_json=None):
        self.template_id = template_id
        self.name = name
        self.creator = creator
        self.template = {}
        if template_json:
            self.parse_template_json(copy.deepcopy(template_json))

    def parse_template_json(self, template_json):
        """
        Parse a template from a json.

        :param template_json: json dict
        """
        if "template" in template_json:
            template_json = template_json.pop("template")

        self.template = template_json

    def template_id(self, keeper):
        return keeper.template_manager.create_template_id(self.contract_name)

    def set_template_id(self, template_id):
        """
        Assign the template id to the template.

        :param template_id: string
        """
        self.template_id = template_id

    def is_template_valid(self, keeper):
        return self.contract_name in keeper.template_manager.get_known_template_names()

    @property
    def fulfillment_order(self):
        """
        List with the fulfillment order.

        :return: list
        """
        return self.template["fulfillmentOrder"]

    @property
    def condition_dependency(self):
        """
        Dictionary with the dependencies of the conditions.

        :return: dict
        """
        return self.template["conditionDependency"]

    @property
    def contract_name(self):
        """
        Contract name of the template.

        :return: string
        """
        return self.template["contractName"]

    @property
    def agreement_events(self):
        """
        List of agreements events.

        :return: list of Event instances
        """
        return [Event(e) for e in self.template["events"]]

    @property
    def conditions(self):
        """
        List of conditions.

        :return: list of ServiceAgreementCondition instances
        """
        return [
            ServiceAgreementCondition(cond_json)
            for cond_json in self.template["conditions"]
        ]

    def set_conditions(self, conditions):
        """
        Set the conditions of the template.

        :param conditions: list of ServiceAgreementCondition instances.
        """
        self.template["conditions"] = [cond.as_dictionary() for cond in conditions]

    def get_event_to_args_map(self, contract_by_name):
        """
        keys in returned dict have the format <contract_name>.<event_name>
        """
        cond_contract_tuples = [
            (cond, contract_by_name[cond.contract_name]) for cond in self.conditions
        ]
        event_to_args = {
            f"{cond.contract_name}.{cond.events[0].name}": (
                contract.get_event_argument_names(cond.events[0].name)
            )
            for cond, contract in cond_contract_tuples
        }

        return event_to_args

    def as_dictionary(self):
        """
        Return the service agreement template as a dictionary.

        :return: dict
        """
        template = {
            "name": self.name,
            "creator": self.creator,
            "serviceAgreementTemplate": {
                "contractName": self.contract_name,
                "events": [e.as_dictionary() for e in self.agreement_events],
                "fulfillmentOrder": self.fulfillment_order,
                "conditionDependency": self.condition_dependency,
                "conditions": [cond.as_dictionary() for cond in self.conditions],
            },
        }

        return template

#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import namedtuple

from ocean_lib.common.agreements.service_agreement_template import (
    ServiceAgreementTemplate,
)
from ocean_lib.common.agreements.service_types import ServiceTypes, ServiceTypesIndices
from ocean_lib.common.ddo.service import Service
from ocean_lib.common.did import did_to_id
from ocean_lib.common.utils.utilities import generate_prefixed_id

Agreement = namedtuple("Agreement", ("template", "conditions"))


class ServiceAgreement(Service):
    """Class representing a Service Agreement."""

    AGREEMENT_TEMPLATE = "serviceAgreementTemplate"
    SERVICE_CONDITIONS = "conditions"

    def __init__(
        self,
        attributes,
        service_agreement_template,
        service_endpoint=None,
        service_type=None,
        service_index=None,
        other_values=None,
    ):
        """

        :param attributes: dict of main attributes of the service. This should
            include `main` and optionally the `additionalInformation` section
        :param service_agreement_template: ServiceAgreementTemplate instance
        :param service_endpoint: str URL to use for requesting service defined in this agreement
        :param service_type: str like ServiceTypes.ASSET_ACCESS
        :param other_values: dict of other key/value that maybe added and will be kept as is.
        """
        self.service_agreement_template = service_agreement_template
        self._other_values = other_values or {}

        service_to_default_index = {
            ServiceTypes.ASSET_ACCESS: ServiceTypesIndices.DEFAULT_ACCESS_INDEX,
            ServiceTypes.CLOUD_COMPUTE: ServiceTypesIndices.DEFAULT_COMPUTING_INDEX,
        }

        try:
            default_index = service_to_default_index[service_type]
        except KeyError:
            raise ValueError(
                f"The service_type {service_type} is not currently supported. Supported "
                f"service types are {ServiceTypes.ASSET_ACCESS} and {ServiceTypes.CLOUD_COMPUTE}"
            )

        service_index = service_index if service_index is not None else default_index
        Service.__init__(
            self,
            service_endpoint,
            service_type,
            attributes,
            other_values,
            service_index,
        )

    @classmethod
    def from_json(cls, service_dict):
        """

        :param service_dict:
        :return:
        """
        service_endpoint, _type, _index, _attributes, service_dict = cls._parse_json(
            service_dict
        )
        template = ServiceAgreementTemplate(
            service_dict.pop("templateId"),
            _attributes["main"]["name"],
            _attributes["main"]["creator"],
            _attributes[cls.AGREEMENT_TEMPLATE],
        )

        return cls(_attributes, template, service_endpoint, _type, _index, service_dict)

    @classmethod
    def from_ddo(cls, service_type, ddo):
        """

        :param service_type: identifier of the service inside the asset DDO, str
        :param ddo:
        :return:
        """
        service_dict = ddo.get_service(service_type).as_dictionary()
        if not service_dict:
            raise ValueError(
                f"Service of type {service_type} is not found in this DDO."
            )

        return cls.from_json(service_dict)

    def as_dictionary(self):
        values = Service.as_dictionary(self)
        values[ServiceAgreementTemplate.TEMPLATE_ID_KEY] = self.template_id
        attributes = values[ServiceAgreement.SERVICE_ATTRIBUTES]
        attributes[
            ServiceAgreement.AGREEMENT_TEMPLATE
        ] = self.service_agreement_template.template
        return values

    def init_conditions_values(self, did, contract_name_to_address):
        param_map = {
            "_documentId": did_to_id(did),
            "_amount": self.attributes["main"]["price"],
            "_rewardAddress": contract_name_to_address["EscrowReward"],
        }
        conditions = self.conditions[:]
        for cond in conditions:
            for param in cond.parameters:
                param.value = param_map.get(param.name, "")

            if cond.timeout > 0:
                cond.timeout = self.attributes["main"]["timeout"]

        self.service_agreement_template.set_conditions(conditions)

    def get_price(self):
        """
        Return the price from the conditions parameters.

        :return: Int
        """
        for cond in self.conditions:
            for p in cond.parameters:
                if p.name == "_amount":
                    return int(p.value)

    @property
    def service_endpoint(self):
        """

        :return:
        """
        return self._service_endpoint

    @property
    def agreement(self):
        """

        :return:
        """
        return Agreement(self.template_id, self.conditions[:])

    @property
    def template_id(self):
        """

        :return:
        """
        return self.service_agreement_template.template_id

    @property
    def conditions(self):
        """

        :return:
        """
        return self.service_agreement_template.conditions

    @property
    def condition_by_name(self):
        """

        :return:
        """
        return {cond.name: cond for cond in self.conditions}

    @property
    def conditions_params_value_hashes(self):
        """

        :return:
        """
        value_hashes = []
        for cond in self.conditions:
            value_hashes.append(cond.values_hash)

        return value_hashes

    @property
    def conditions_timeouts(self):
        """

        :return:
        """
        return [cond.timeout for cond in self.conditions]

    @property
    def conditions_timelocks(self):
        """

        :return:
        """
        return [cond.timelock for cond in self.conditions]

    @property
    def conditions_contracts(self):
        """

        :return:
        """
        return [cond.contract_name for cond in self.conditions]

    @staticmethod
    def generate_service_agreement_hash(
        template_id, values_hash_list, timelocks, timeouts, agreement_id, hash_function
    ):
        """

        :param template_id:
        :param values_hash_list:
        :param timelocks:
        :param timeouts:
        :param agreement_id: id of the agreement, hex str
        :param hash_function: reference to function that will be used to compute the hash (sha3
        or similar)
        :return:
        """
        return hash_function(
            ["bytes32", "bytes32[]", "uint256[]", "uint256[]", "bytes32"],
            [template_id, values_hash_list, timelocks, timeouts, agreement_id],
        )

    @staticmethod
    def create_new_agreement_id():
        """

        :return:
        """
        return generate_prefixed_id()

    def generate_agreement_condition_ids(
        self, agreement_id, asset_id, consumer_address, publisher_address, keeper
    ):
        """

        :param agreement_id: id of the agreement, hex str
        :param asset_id:
        :param consumer_address: ethereum account address of consumer, hex str
        :param publisher_address: ethereum account address of publisher, hex str
        :param keeper:
        :return:
        """
        lock_cond_id = keeper.lock_reward_condition.generate_id(
            agreement_id,
            self.condition_by_name["lockReward"].param_types,
            [keeper.escrow_reward_condition.address, self.get_price()],
        ).hex()

        if self.type == ServiceTypes.ASSET_ACCESS:
            access_or_compute_id = keeper.access_secret_store_condition.generate_id(
                agreement_id,
                self.condition_by_name["accessSecretStore"].param_types,
                [asset_id, consumer_address],
            ).hex()
        elif self.type == ServiceTypes.CLOUD_COMPUTE:
            access_or_compute_id = keeper.compute_execution_condition.generate_id(
                agreement_id,
                self.condition_by_name["computeExecution"].param_types,
                [asset_id, consumer_address],
            ).hex()
        else:
            raise Exception(
                "Error generating the condition ids, the service_agreement type is not valid."
            )

        escrow_cond_id = keeper.escrow_reward_condition.generate_id(
            agreement_id,
            self.condition_by_name["escrowReward"].param_types,
            [
                self.get_price(),
                publisher_address,
                consumer_address,
                lock_cond_id,
                access_or_compute_id,
            ],
        ).hex()

        return lock_cond_id, access_or_compute_id, escrow_cond_id

    def get_service_agreement_hash(
        self, agreement_id, asset_id, consumer_address, publisher_address, keeper
    ):
        """Return the hash of the service agreement values to be signed by a consumer.

        :param agreement_id:id of the agreement, hex str
        :param asset_id:
        :param consumer_address: ethereum account address of consumer, hex str
        :param publisher_address: ethereum account address of publisher, hex str
        :param keeper:
        :return:
        """
        agreement_hash = ServiceAgreement.generate_service_agreement_hash(
            self.template_id,
            self.generate_agreement_condition_ids(
                agreement_id, asset_id, consumer_address, publisher_address, keeper
            ),
            self.conditions_timelocks,
            self.conditions_timeouts,
            agreement_id,
            keeper.generate_multi_value_hash,
        )
        return agreement_hash

from ocean_utils.agreements.service_agreement import ServiceAgreement as BaseServiceAgreement


class ServiceAgreement(BaseServiceAgreement):
    def get_price(self):
        return self.main.get('cost', self.attributes.get('cost', 0))

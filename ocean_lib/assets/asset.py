from ocean_utils.ddo.ddo import DDO


class Asset(DDO):
    @property
    def data_token_address(self):
        return self._other_values['dataTokenAddress']

    @data_token_address.setter
    def data_token_address(self, token_address):
        self._other_values['dataTokenAddress'] = token_address

    @property
    def values(self):
        return self._other_values.copy()

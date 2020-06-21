
class OceanMarket:
    def __init__(self, config, data_provider):
        self._config = config
        self._data_provider = data_provider

    def buy_data_tokens(self, token_address, amount, price, currency):
        return ''

    def get_data_token_price(self, token_address):
        return 50, 'ocean'

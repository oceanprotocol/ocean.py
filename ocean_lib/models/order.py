from collections import namedtuple

Order = namedtuple(
    'Order',
    (
        'datatoken', 'amount', 'timestamp', 'transactionId', 'did', 'payer', 'consumer', 'serviceId', 'serviceType'
    )
)

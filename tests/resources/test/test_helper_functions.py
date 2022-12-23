from tests.resources.helper_functions import convert_bt_amt_to_dt


def test_convert_bt_amt_to_dt():
    bt_decimals = 16
    bt_amt_float = 10.0
    price_float = 2.0  # price

    expected_dt_amt_float = bt_amt_float / price_float

    bt_amt_wei = int(bt_amt_float * 10**bt_decimals)
    bt_per_dt_float = 1.0 / price_float
    dt_per_bt_wei = int(bt_per_dt_float * 10**18)

    dt_amt_wei = convert_bt_amt_to_dt(bt_amt_wei, bt_decimals, dt_per_bt_wei)
    dt_amt_float = float(dt_amt_wei / 10**18)

    assert dt_amt_float == expected_dt_amt_float

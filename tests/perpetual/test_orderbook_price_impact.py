import decimal
from unittest import TestCase

from x10.perpetual.configuration import TESTNET_CONFIG
from x10.perpetual.orderbook import OrderBook
from x10.perpetual.orderbooks import OrderbookUpdateModel


class TestOrderBook(TestCase):
    def setUp(self):
        self.endpoint_config = TESTNET_CONFIG
        self.market_name = "dummy-market"
        self.orderbook = OrderBook(
            self.endpoint_config,
            self.market_name,
            best_ask_change_callback=None,
            best_bid_change_callback=None,
        )
        self.populate_dummy_data()

    def populate_dummy_data(self):
        dummy_data = OrderbookUpdateModel(
            market=self.market_name,
            bid=[
                {"price": decimal.Decimal("100"), "qty": decimal.Decimal("1")},
                {"price": decimal.Decimal("99"), "qty": decimal.Decimal("2")},
                {"price": decimal.Decimal("98"), "qty": decimal.Decimal("1")},
            ],
            ask=[
                {"price": decimal.Decimal("101"), "qty": decimal.Decimal("1")},
                {"price": decimal.Decimal("102"), "qty": decimal.Decimal("2")},
                {"price": decimal.Decimal("103"), "qty": decimal.Decimal("1")},
            ],
        )
        self.orderbook.update_orderbook(dummy_data)

    def test_calculate_impact_partial_buy(self):
        notional = decimal.Decimal("105")
        expected_amount = decimal.Decimal("1") + decimal.Decimal("4") / decimal.Decimal("102")
        expected_average_price = notional / expected_amount
        result = self.orderbook.calculate_price_impact_notional(notional, "BUY")
        self.assertEqual(result.amount, expected_amount)
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_impact_partial_sell(self):
        notional = decimal.Decimal("110")
        expected_amount = decimal.Decimal(1) + decimal.Decimal("10") / decimal.Decimal("99")
        expected_average_price = notional / expected_amount
        result = self.orderbook.calculate_price_impact_notional(notional, "SELL")
        self.assertEqual(result.amount, expected_amount)
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_price_impact_total_match_sell(self):
        notional = decimal.Decimal("199")
        expected_amount = decimal.Decimal("2")
        expected_average_price = notional / expected_amount
        result = self.orderbook.calculate_price_impact_notional(notional, "SELL")
        self.assertEqual(result.amount, expected_amount)
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_price_impact_total_match_buy(self):
        notional = decimal.Decimal("101") + decimal.Decimal("2") * decimal.Decimal("102") + decimal.Decimal("103")
        expected_amount = decimal.Decimal("4")
        expected_average_price = notional / expected_amount
        result = self.orderbook.calculate_price_impact_notional(notional, "BUY")
        self.assertEqual(result.amount, expected_amount)
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_price_impact_insufficient_liquidity_bid(self):
        notional = decimal.Decimal("1000")
        result = self.orderbook.calculate_price_impact_notional(notional, "SELL")
        self.assertIsNone(result)

    def test_calculate_price_impact_insufficient_liquidity_ask(self):
        notional = decimal.Decimal("1000")
        result = self.orderbook.calculate_price_impact_notional(notional, "BUY")
        self.assertIsNone(result)

    def test_calculate_price_impact_invalid_notional(self):
        notional = decimal.Decimal("-10")
        result = self.orderbook.calculate_price_impact_notional(notional, "SELL")
        self.assertIsNone(result)

    def test_calculate_price_impact_invalid_side(self):
        notional = decimal.Decimal("100")
        result = self.orderbook.calculate_price_impact_notional(notional, "invalid")
        self.assertIsNone(result)

    def test_calculate_qty_impact_partial_buy(self):
        """
        Buy a partial quantity that spans multiple ask levels.
        For example: buying 2 units:
          - 1 unit at price 101
          - 1 unit at price 102
        total cost = 101 + 102 = 203
        average price = 203 / 2 = 101.5
        """
        qty = decimal.Decimal("2")
        result = self.orderbook.calculate_price_impact_qty(qty, "BUY")

        self.assertIsNotNone(result, "Result should not be None for partial fill.")
        self.assertEqual(result.amount, qty, "Filled amount should match requested qty.")

        expected_average_price = decimal.Decimal("101.5")
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_qty_impact_partial_sell(self):
        """
        Sell a partial quantity that spans multiple bid levels.
        For example: selling 2 units:
          - 1 unit at price 100
          - 1 unit at price 99
        total received = 100 + 99 = 199
        average price = 199 / 2 = 99.5
        """
        qty = decimal.Decimal("2")
        result = self.orderbook.calculate_price_impact_qty(qty, "SELL")

        self.assertIsNotNone(result, "Result should not be None for partial fill.")
        self.assertEqual(result.amount, qty, "Filled amount should match requested qty.")

        expected_average_price = decimal.Decimal("99.5")
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_qty_impact_total_match_buy(self):
        """
        Buy all available ask liquidity: total ask qty = 1 + 2 + 1 = 4
        Fill:
          - 1 @101 => cost 101
          - 2 @102 => cost 204
          - 1 @103 => cost 103
        total = 101 + 204 + 103 = 408
        average = 408 / 4 = 102
        """
        qty = decimal.Decimal("4")
        result = self.orderbook.calculate_price_impact_qty(qty, "BUY")

        self.assertIsNotNone(result, "Result should not be None when liquidity matches exactly.")
        self.assertEqual(result.amount, qty, "Filled amount should match requested qty.")

        expected_average_price = decimal.Decimal("102")
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_qty_impact_total_match_sell(self):
        """
        Sell all available bid liquidity: total bid qty = 1 + 2 + 1 = 4
        Fill:
          - 1 @100 => 100
          - 2 @99 => 198
          - 1 @98 => 98
        total = 100 + 198 + 98 = 396
        average = 396 / 4 = 99
        """
        qty = decimal.Decimal("4")
        result = self.orderbook.calculate_price_impact_qty(qty, "SELL")

        self.assertIsNotNone(result, "Result should not be None when liquidity matches exactly.")
        self.assertEqual(result.amount, qty)

        expected_average_price = decimal.Decimal("99")
        self.assertEqual(result.price, expected_average_price)

    def test_calculate_qty_impact_insufficient_liquidity_buy(self):
        """
        Request a qty larger than available on the ask side (4 total).
        Asking for 5 => insufficient => should return None.
        """
        qty = decimal.Decimal("5")
        result = self.orderbook.calculate_price_impact_qty(qty, "BUY")
        self.assertIsNone(result, "Result should be None when there's insufficient ask liquidity.")

    def test_calculate_qty_impact_insufficient_liquidity_sell(self):
        """
        Request a qty larger than available on the bid side (4 total).
        Asking for 5 => insufficient => should return None.
        """
        qty = decimal.Decimal("5")
        result = self.orderbook.calculate_price_impact_qty(qty, "SELL")
        self.assertIsNone(result, "Result should be None when there's insufficient bid liquidity.")

    def test_calculate_qty_impact_invalid_qty(self):
        """
        Negative or zero qty should return None.
        """
        qty = decimal.Decimal("-1")
        result = self.orderbook.calculate_price_impact_qty(qty, "BUY")
        self.assertIsNone(result, "Result should be None for invalid qty (negative).")

        qty_zero = decimal.Decimal("0")
        result_zero = self.orderbook.calculate_price_impact_qty(qty_zero, "SELL")
        self.assertIsNone(result_zero, "Result should be None for invalid qty (zero).")

    def test_calculate_qty_impact_invalid_side(self):
        """
        Any side not 'BUY' or 'SELL' should yield None.
        """
        qty = decimal.Decimal("1")
        result = self.orderbook.calculate_price_impact_qty(qty, "INVALID_SIDE")
        self.assertIsNone(result, "Result should be None for invalid side.")

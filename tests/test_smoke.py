"""A small starting test suite for the order desk."""

from pathlib import Path
import tempfile
import unittest

from supplydesk.service import OrderService


class OrderSmokeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    def test_regular_pickup_quote(self):
        quote = self.service.quote("regular", [{"product_id": "notebook", "quantity": 2}])
        self.assertEqual(quote["subtotal_cents"], 1000)
        self.assertEqual(quote["discount_cents"], 0)
        self.assertEqual(quote["delivery_cents"], 0)
        self.assertEqual(quote["total_cents"], 1000)

    def test_student_delivery_quote(self):
        quote = self.service.quote("student", [{"product_id": "hoodie", "quantity": 2}], "delivery")
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 600)
        self.assertEqual(quote["total_cents"], 7800)

    def test_order_can_be_reopened(self):
        order = self.service.place_order("regular", [{"product_id": "mug", "quantity": 1}])
        self.assertEqual(order["order_id"], "ORD-0001")
        self.assertEqual(order["status"], "placed")
        self.assertEqual(OrderService(self.path).get_order(order["order_id"]), order)

    def test_cancel_order_restores_stock(self):
        before = self.service.catalog()
        order = self.service.place_order("regular", [{"product_id": "pen-pack", "quantity": 2}])
        cancelled = self.service.cancel_order(order["order_id"])
        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.service.catalog(), before)


if __name__ == "__main__":
    unittest.main()

# generated smoke tests: 

    # Test that express delivery adds a fixed $12.00 fee
    def test_express_delivery_quote(self):
        quote = self.service.quote(
            "regular",
            [{"product_id": "notebook", "quantity": 2}],
            "express"
        )

        self.assertEqual(quote["subtotal_cents"], 1000)
        self.assertEqual(quote["discount_cents"], 0)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 2200)

    # Test that student discounts apply to merchandise, not delivery
    def test_student_express_delivery_quote(self):
        quote = self.service.quote(
            "student",
            [{"product_id": "hoodie", "quantity": 2}],
            "express"
        )

        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 8400)

    # Test that an express order can be saved and retrieved
    def test_express_order_can_be_reopened(self):
        order = self.service.place_order(
            "regular",
            [{"product_id": "notebook", "quantity": 2}],
            "express"
        )

        # Create a new service using the same saved data file
        reopened_service = OrderService(self.path)
        saved_order = reopened_service.get_order(order["order_id"])

        self.assertEqual(saved_order["fulfillment"], "express")
        self.assertEqual(saved_order["delivery_cents"], 1200)
        self.assertEqual(saved_order["total_cents"], 2200)

    # Test that cancelling an express order restores product stock
    def test_cancel_express_order_restores_stock(self):
        before = self.service.catalog()

        order = self.service.place_order(
            "regular",
            [{"product_id": "notebook", "quantity": 2}],
            "express"
        )

        self.service.cancel_order(order["order_id"])

        self.assertEqual(self.service.catalog(), before)
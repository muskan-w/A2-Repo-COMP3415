
"""Operations used by the command-line order desk."""

from supplydesk.storage import JsonStore

#generated

class OrderService:
    def __init__(self, state_path=".supplydesk/state.json"):
        self.store = JsonStore(state_path)

    def catalog(self):
        return self.store.load()["catalog"]

    # Refactoring 1: Shared quote calculation  

    def _build_quote(self, state, customer_type, items, fulfillment):
        # Check that the customer type and fulfillment are valid
        if customer_type not in ("regular", "student"):
            raise ValueError("Customer type must be regular or student.")
        if fulfillment not in ("pickup", "delivery"):
            raise ValueError("Fulfillment must be pickup or delivery.")

        # Make sure the order contains at least one item
        if not isinstance(items, list) or not items:
            raise ValueError("An order must contain at least one item.")

        lines = []
        subtotal = 0

        # Check each item and calculate its price
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Each item must contain a product_id and quantity.")

            product = None
            for candidate in state["catalog"]:
                if candidate["product_id"] == item.get("product_id"):
                    product = candidate
                    break

            if product is None:
                raise ValueError("Unknown product.")

            quantity = item.get("quantity")
            if type(quantity) is not int or quantity < 1 or quantity > 99:
                raise ValueError("Quantity must be an integer from 1 to 99.")

            if quantity > product["stock"]:
                raise ValueError("Not enough stock for " + product["product_id"] + ".")

            line_total = product["unit_price_cents"] * quantity
            subtotal += line_total

            lines.append({
                "product_id": product["product_id"],
                "name": product["name"],
                "unit_price_cents": product["unit_price_cents"],
                "quantity": quantity,
                "line_total_cents": line_total,
            })

        # Calculate the student discount
        discount = 0
        if customer_type == "student" and subtotal > 5000:
            discount = (subtotal * 10 + 50) // 100

        # Calculate the delivery fee
        delivery = 0
        if fulfillment == "delivery" and subtotal - discount < 10000:
            delivery = 600

        # Return the quote information
        return {
            "customer_type": customer_type,
            "fulfillment": fulfillment,
            "items": lines,
            "subtotal_cents": subtotal,
            "discount_cents": discount,
            "delivery_cents": delivery,
            "total_cents": subtotal - discount + delivery,
        }

    def quote(self, customer_type, items, fulfillment="pickup"):
        state = self.store.load()

        # Use the shared helper to calculate the quote
        return self._build_quote(state, customer_type, items, fulfillment)

        # Refactoring 2
    def _create_order_record(self, state, quote):
        # Build the order using the next available order number
        order = {
            "order_id": "ORD-" + str(state["next_order_number"]).zfill(4),
            "status": "placed",
            "customer_type": quote["customer_type"],
            "fulfillment": quote["fulfillment"],
            "items": quote["items"],
            "subtotal_cents": quote["subtotal_cents"],
            "discount_cents": quote["discount_cents"],
            "delivery_cents": quote["delivery_cents"],
            "total_cents": quote["total_cents"],
        }

        return order

    # Update the stock after an order has been created
    def _update_stock(self, state, items):
        # Go through each item in the order
        for line in items:
            # Find the matching product in the catalog
            for product in state["catalog"]:
                if product["product_id"] == line["product_id"]:
                    # Reduce the available stock by the ordered quantity
                    product["stock"] -= line["quantity"]

    def place_order(self, customer_type, items, fulfillment="pickup"):
        state = self.store.load()

        # Calculate the quote using the shared helper
        quote = self._build_quote(state, customer_type, items, fulfillment)

        # Calculate the quote using the shared helper
        quote = self._build_quote(state, customer_type, items, fulfillment)

        # Create the order record using the calculated quote
        order = self._create_order_record(state, quote)

        # Update the inventory after the order is created
        self._update_stock(state, quote["items"])

        # Update the order number and add the order to storage
        state["next_order_number"] += 1
        state["orders"].append(order)

        # Save the updated data
        self.store.save(state)

        return order
        
    def list_orders(self):
        return self.store.load()["orders"]

    def get_order(self, order_id):
        state = self.store.load()
        for order in state["orders"]:
            if order["order_id"] == order_id:
                return order
        raise ValueError("Unknown order: " + order_id)

    def cancel_order(self, order_id):
        state = self.store.load()
        order = None
        for candidate in state["orders"]:
            if candidate["order_id"] == order_id:
                order = candidate
                break

        if order is None:
            raise ValueError("Unknown order: " + order_id)

        for line in order["items"]:
            for product in state["catalog"]:
                if product["product_id"] == line["product_id"]:
                    product["stock"] += line["quantity"]

        order["status"] = "cancelled"
        self.store.save(state)
        return order

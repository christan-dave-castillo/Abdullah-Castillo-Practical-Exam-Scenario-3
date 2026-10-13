"""Run with: python -m unittest discover -s tests -v (no display needed)."""

import unittest
from decimal import Decimal

from pos_logic import POS, POSError, PRODUCTS, money


class POSTests(unittest.TestCase):
    def setUp(self):
        self.pos = POS()

    def pay(self, cash="200.00"):
        self.pos.set_cash(cash)
        return self.pos.validate_payment()

    def test_exact_six_product_catalog(self):
        expected = [
            ("Classic Milk Tea (Regular)", "59.00"),
            ("Wintermelon Milk Tea (Regular)", "65.00"),
            ("Taro Milk Tea (Regular)", "65.00"),
            ("Fruit Tea — Lychee (Regular)", "55.00"),
            ("Brown Sugar Milk Tea (Regular)", "69.00"),
            ("Bottled Water", "20.00"),
        ]
        self.assertEqual([(p.name, p.price) for p in PRODUCTS], [
            (name, Decimal(price)) for name, price in expected
        ])
        self.assertEqual(len({p.id for p in PRODUCTS}), 6)

    def test_empty_cart_total_and_state(self):
        self.assertEqual(self.pos.items, ())
        self.assertEqual(self.pos.total, Decimal("0.00"))
        self.assertIsInstance(self.pos.total, Decimal)
        self.assertIsNone(self.pos.change)
        self.assertFalse(self.pos.confirmed)
        self.assertEqual(self.pos.receipt, "")

    def test_add_merges_quantities_and_computes_subtotal(self):
        self.pos.add("classic")
        self.pos.add("classic")
        self.pos.add("water")
        self.assertEqual(len(self.pos.items), 2)
        self.assertEqual(self.pos.items[0].quantity, 2)
        self.assertEqual(self.pos.items[0].subtotal, Decimal("118.00"))
        self.assertEqual(self.pos.total, Decimal("138.00"))

    def test_all_products_total(self):
        for product in PRODUCTS:
            self.pos.add(product.id)
        self.assertEqual(self.pos.total, Decimal("333.00"))

    def test_increase_decrease_and_remove(self):
        self.pos.add("taro")
        self.pos.increase("taro")
        self.assertEqual(self.pos.total, Decimal("130.00"))
        self.pos.decrease("taro")
        self.assertEqual(self.pos.items[0].quantity, 1)
        self.assertEqual(self.pos.total, Decimal("65.00"))
        self.pos.remove("taro")
        self.assertEqual(self.pos.items, ())
        self.assertEqual(self.pos.total, Decimal("0.00"))

    def test_decrease_last_unit_removes_row(self):
        self.pos.add("water")
        self.pos.decrease("water")
        self.assertEqual(self.pos.items, ())
        with self.assertRaises(POSError):
            self.pos.decrease("water")

    def test_unknown_product_and_missing_cart_selection(self):
        with self.assertRaisesRegex(POSError, "Unknown product"):
            self.pos.add("unknown")
        for action in (self.pos.increase, self.pos.decrease, self.pos.remove):
            with self.subTest(action=action.__name__):
                with self.assertRaisesRegex(POSError, "in the cart"):
                    action("water")
        self.assertEqual(self.pos.total, Decimal("0.00"))

    def test_empty_cart_cannot_be_paid_or_confirmed(self):
        self.pos.set_cash("200")
        with self.assertRaisesRegex(POSError, "Add at least one product"):
            self.pos.validate_payment()
        with self.assertRaisesRegex(POSError, "Validate"):
            self.pos.confirm_payment()

    def test_blank_payment_rejected(self):
        self.pos.add("classic")
        for text in ("", " ", "\t\n"):
            with self.subTest(cash=text):
                with self.assertRaisesRegex(POSError, "blank"):
                    self.pay(text)
                self.assertIsNone(self.pos.validated_cash)

    def test_negative_payment_rejected(self):
        self.pos.add("classic")
        for text in ("-1", "-0.01", "-200.00"):
            with self.subTest(cash=text):
                with self.assertRaisesRegex(POSError, "negative"):
                    self.pay(text)

    def test_non_numeric_and_unsafe_forms_rejected(self):
        self.pos.add("classic")
        for text in ("abc", "NaN", "sNaN", "Infinity", "inf", "1e3", "₱200",
                     "1,000", "200.001", "1+2", "open('x')", "２００", "200\n.00"):
            with self.subTest(cash=text):
                with self.assertRaisesRegex(POSError, "numeric"):
                    self.pay(text)
                self.assertIsNone(self.pos.validated_cash)
                self.assertIsNone(self.pos.change)

    def test_excessively_long_payment_rejected(self):
        self.pos.add("classic")
        with self.assertRaisesRegex(POSError, "too long"):
            self.pay("9" * 1000)

    def test_zero_and_insufficient_cash_rejected_with_total(self):
        self.pos.add("classic")
        for cash in ("0", "58", "58.99"):
            with self.subTest(cash=cash):
                with self.assertRaisesRegex(POSError, "Insufficient payment.*₱59.00"):
                    self.pay(cash)

    def test_exact_payment_has_zero_change(self):
        self.pos.add("classic")
        self.assertEqual(self.pay("59.00"), Decimal("0.00"))
        self.assertEqual(self.pos.change, Decimal("0.00"))
        self.assertEqual(self.pos.validated_cash, Decimal("59.00"))

    def test_decimal_cents_and_surrounding_spaces(self):
        self.pos.add("classic")
        self.assertEqual(self.pay(" 100.50 "), Decimal("41.50"))
        self.assertIsInstance(self.pos.change, Decimal)
        self.assertEqual(self.pay("100.5"), Decimal("41.50"))

    def test_cart_changes_invalidate_payment(self):
        for action, product_id in (("add", "water"), ("increase", "classic"),
                                   ("decrease", "classic"), ("remove", "classic")):
            with self.subTest(action=action):
                self.pos.new_transaction()
                self.pos.add("classic")
                self.pos.add("classic")
                self.pay()
                getattr(self.pos, action)(product_id)
                self.assertIsNone(self.pos.validated_cash)
                self.assertIsNone(self.pos.change)
                with self.assertRaisesRegex(POSError, "Validate"):
                    self.pos.confirm_payment()

    def test_cash_changes_require_revalidation_even_if_changed_back(self):
        self.pos.add("classic")
        self.pay("100")
        self.pos.set_cash("200")
        self.pos.set_cash("100")
        self.assertIsNone(self.pos.validated_cash)
        self.assertIsNone(self.pos.change)
        with self.assertRaisesRegex(POSError, "Validate"):
            self.pos.confirm_payment()
        self.assertEqual(self.pos.validate_payment(), Decimal("41.00"))

    def test_same_cash_value_preserves_validation(self):
        self.pos.add("classic")
        self.pay("100")
        self.pos.set_cash("100")
        self.assertEqual(self.pos.validated_cash, Decimal("100.00"))

    def test_failed_payment_does_not_reuse_previous_validation(self):
        self.pos.add("classic")
        self.pay("100")
        self.pos.set_cash("wrong")
        with self.assertRaises(POSError):
            self.pos.validate_payment()
        with self.assertRaises(POSError):
            self.pos.confirm_payment()
        self.assertFalse(self.pos.confirmed)
        self.assertEqual(self.pos.receipt, "")

    def test_confirm_requires_validation_first(self):
        self.pos.add("classic")
        self.pos.set_cash("200")
        with self.assertRaisesRegex(POSError, "Validate"):
            self.pos.confirm_payment()
        self.assertEqual(self.pos.reference, "")

    def test_complete_transaction_and_receipt(self):
        for product_id in ("classic", "classic", "lychee", "water"):
            self.pos.add(product_id)
        self.assertEqual(self.pos.total, Decimal("193.00"))
        self.assertEqual(self.pay(), Decimal("7.00"))
        self.assertEqual(self.pos.receipt, "")  # Validation does not complete a sale.
        receipt = self.pos.confirm_payment()
        self.assertTrue(self.pos.confirmed)
        self.assertRegex(self.pos.reference, r"^MT-[0-9A-F]{12}$")
        for line in (self.pos.reference, "Classic Milk Tea (Regular)",
                     "Qty 2 × ₱59.00 = ₱118.00", "Fruit Tea — Lychee (Regular)",
                     "Qty 1 × ₱55.00 = ₱55.00", "Bottled Water",
                     "Qty 1 × ₱20.00 = ₱20.00", "TOTAL: ₱193.00",
                     "Cash paid: ₱200.00", "Change: ₱7.00", "Payment confirmed"):
            self.assertIn(line, receipt)
        self.assertEqual(receipt, self.pos.receipt)

    def test_duplicate_confirmation_rejected_without_changing_receipt(self):
        self.pos.add("water")
        self.pay()
        receipt = self.pos.confirm_payment()
        reference = self.pos.reference
        with self.assertRaisesRegex(POSError, "already confirmed"):
            self.pos.confirm_payment()
        self.assertEqual(self.pos.reference, reference)
        self.assertEqual(self.pos.receipt, receipt)

    def test_completed_transaction_cannot_be_edited_or_revalidated(self):
        self.pos.add("classic")
        self.pay()
        self.pos.confirm_payment()
        for action, args in ((self.pos.add, ("water",)), (self.pos.increase, ("classic",)),
                             (self.pos.decrease, ("classic",)), (self.pos.remove, ("classic",)),
                             (self.pos.set_cash, ("300",)), (self.pos.validate_payment, ())):
            with self.subTest(action=action.__name__):
                with self.assertRaisesRegex(POSError, "already confirmed"):
                    action(*args)
        self.assertEqual(self.pos.total, Decimal("59.00"))
        self.assertEqual(self.pos.cash_text, "200.00")

    def test_new_transaction_clears_everything_and_can_sell_again(self):
        self.pos.add("classic")
        self.pay()
        self.pos.confirm_payment()
        previous_reference = self.pos.reference
        self.pos.new_transaction()
        self.assertEqual(self.pos.items, ())
        self.assertEqual(self.pos.total, Decimal("0.00"))
        self.assertEqual(self.pos.cash_text, "")
        self.assertEqual(self.pos.receipt, "")
        self.assertEqual(self.pos.reference, "")
        self.assertIsNone(self.pos.validated_cash)
        self.assertIsNone(self.pos.change)
        self.assertFalse(self.pos.confirmed)
        self.pos.add("water")
        self.pay("20")
        self.pos.confirm_payment()
        self.assertNotEqual(self.pos.reference, previous_reference)
        self.assertEqual(self.pos.total, Decimal("20.00"))

    def test_new_transaction_clears_unconfirmed_validation(self):
        self.pos.add("water")
        self.pay()
        self.pos.new_transaction()
        self.assertIsNone(self.pos.validated_cash)
        with self.assertRaises(POSError):
            self.pos.confirm_payment()

    def test_money_formatting(self):
        self.assertEqual(money(Decimal("7")), "₱7.00")
        self.assertEqual(money(Decimal("1000.50")), "₱1,000.50")


if __name__ == "__main__":
    unittest.main()

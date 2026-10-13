"""Real Tkinter widget tests; skipped when no display is available.

Dialogs are mocked to avoid blocking the suite. Their requested content is
checked, but native dialog appearance still needs manual desktop verification.
"""

import tkinter as tk
import unittest
from unittest.mock import patch

from main import POSApp


class GUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tkinter display unavailable: {error}")
        probe.destroy()

    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.root.destroy)
        self.callback_errors = []
        self.root.report_callback_exception = lambda *error: self.callback_errors.append(error)
        self.app = POSApp(self.root)
        self.errors = self.mock_dialog("showerror")
        self.success = self.mock_dialog("showinfo")
        self.confirm = self.mock_dialog("askyesno", return_value=True)
        self.root.update()

    def mock_dialog(self, name, **kwargs):
        patcher = patch(f"main.messagebox.{name}", **kwargs)
        result = patcher.start()
        self.addCleanup(patcher.stop)
        return result

    def tearDown(self):
        self.root.update()
        self.assertEqual(self.callback_errors, [], "A Tkinter callback raised an exception")

    def make_order(self):
        for index in (0, 0, 3, 5):
            self.app.product_buttons[index].invoke()

    def validate(self, cash="200.00"):
        self.app.cash_entry.delete(0, "end")
        self.app.cash_entry.insert(0, cash)
        self.app.validate_button.invoke()

    def assert_confirmation_disabled(self):
        self.assertTrue(self.app.confirm_button.instate(["disabled"]))
        self.assertEqual(self.app.change.get(), "Change: —")

    def test_catalog_buttons_and_order_summary(self):
        self.assertEqual(len(self.app.product_buttons), 6)
        self.make_order()
        self.assertEqual(self.app.cart.get_children(), ("classic", "lychee", "water"))
        self.assertEqual(tuple(self.app.cart.item("classic", "values")), (
            "Classic Milk Tea (Regular)", "2", "₱59.00", "₱118.00",
        ))
        self.assertEqual(self.app.total.get(), "Total: ₱193.00")
        self.assertIn("Item added", self.app.status.get())

    def test_cart_quantity_and_remove_buttons(self):
        self.app.product_buttons[0].invoke()
        self.app.cart.selection_set("classic")
        self.app.cart_buttons[0].invoke()
        self.assertEqual(self.app.total.get(), "Total: ₱118.00")
        self.app.cart_buttons[1].invoke()
        self.assertEqual(self.app.total.get(), "Total: ₱59.00")
        self.app.cart_buttons[2].invoke()
        self.assertEqual(self.app.cart.get_children(), ())
        self.assertEqual(self.app.total.get(), "Total: ₱0.00")

    def test_decrease_last_item_removes_visible_row(self):
        self.app.product_buttons[5].invoke()
        self.app.cart_buttons[1].invoke()
        self.assertEqual(self.app.cart.get_children(), ())
        self.assertEqual(self.app.total.get(), "Total: ₱0.00")

    def test_cart_action_without_selection_alerts(self):
        self.app.cart_buttons[0].invoke()
        self.errors.assert_called_once()
        self.assertIn("Select a cart item first", self.errors.call_args.args[1])

    def test_empty_order_payment_alerts(self):
        self.validate()
        self.assertIn("Add at least one product", self.errors.call_args.args[1])
        self.assert_confirmation_disabled()

    def test_invalid_cash_alerts_and_disables_confirmation(self):
        self.make_order()
        for cash, message in (("", "blank"), ("abc", "numeric"),
                              ("-1", "negative"), ("192.99", "Insufficient"),
                              ("NaN", "numeric"), ("200.001", "numeric")):
            with self.subTest(cash=cash):
                self.validate(cash)
                self.assertIn(message, self.errors.call_args.args[1])
                self.assert_confirmation_disabled()
                self.assertEqual(self.app.receipt.get("1.0", "end-1c"), "")

    def test_valid_cash_enables_confirmation_and_shows_change(self):
        self.make_order()
        self.validate()
        self.assertEqual(self.app.change.get(), "Change: ₱7.00")
        self.assertFalse(self.app.confirm_button.instate(["disabled"]))
        self.errors.assert_not_called()

    def test_enter_key_validates_cash(self):
        self.make_order()
        self.root.focus_force()
        self.app.cash_entry.focus_set()
        self.app.cash_entry.insert(0, "200")
        self.root.update()
        self.app.cash_entry.event_generate("<Return>")
        self.root.update()
        self.assertEqual(self.app.change.get(), "Change: ₱7.00")
        self.assertFalse(self.app.confirm_button.instate(["disabled"]))

    def test_exact_cash_can_be_confirmed(self):
        self.make_order()
        self.validate("193.00")
        self.assertEqual(self.app.change.get(), "Change: ₱0.00")
        self.app.confirm_button.invoke()
        self.assertTrue(self.app.pos.confirmed)
        self.success.assert_called_once()

    def test_cash_and_cart_changes_disable_confirmation(self):
        self.make_order()
        self.validate()
        self.app.cash_entry.insert("end", "0")
        self.assert_confirmation_disabled()
        self.validate()
        self.app.product_buttons[5].invoke()
        self.assert_confirmation_disabled()

    def test_cancel_confirmation_keeps_transaction_open(self):
        self.make_order()
        self.validate()
        self.confirm.return_value = False
        self.app.confirm_button.invoke()
        self.assertFalse(self.app.pos.confirmed)
        self.assertEqual(self.app.receipt.get("1.0", "end-1c"), "")
        self.assertFalse(self.app.confirm_button.instate(["disabled"]))
        self.success.assert_not_called()

    def test_complete_flow_receipt_and_new_transaction(self):
        self.make_order()
        self.validate()
        self.app.confirm_button.invoke()
        details = self.confirm.call_args.args[1]
        self.assertIn("2 × Classic Milk Tea (Regular): ₱118.00", details)
        self.assertIn("Total: ₱193.00", details)
        self.assertIn("Cash paid: ₱200.00", details)
        self.assertIn("Change: ₱7.00", details)
        receipt = self.app.receipt.get("1.0", "end-1c")
        self.assertEqual(receipt, self.app.pos.receipt)
        self.assertIn(self.app.pos.reference, receipt)
        self.assertIn("TOTAL: ₱193.00", receipt)
        self.assertIn("Cash paid: ₱200.00", receipt)
        self.assertIn("Change: ₱7.00", receipt)
        self.assertIn("Payment successful", self.app.status.get())
        self.success.assert_called_once()
        self.assertTrue(self.app.confirm_button.instate(["disabled"]))
        self.assertTrue(self.app.cash_entry.instate(["disabled"]))
        self.assertTrue(self.app.validate_button.instate(["disabled"]))
        for button in self.app.product_buttons + self.app.cart_buttons:
            self.assertTrue(button.instate(["disabled"]))
        self.app.confirm_button.invoke()  # Disabled button cannot confirm again.
        self.success.assert_called_once()
        self.app.new_transaction()
        self.assertEqual(self.app.cart.get_children(), ())
        self.assertEqual(self.app.total.get(), "Total: ₱0.00")
        self.assertEqual(self.app.cash.get(), "")
        self.assertEqual(self.app.receipt.get("1.0", "end-1c"), "")
        self.assert_confirmation_disabled()
        self.assertFalse(self.app.cash_entry.instate(["disabled"]))
        self.app.product_buttons[5].invoke()
        self.validate("20")
        self.app.confirm_button.invoke()
        self.assertTrue(self.app.pos.confirmed)
        self.assertEqual(self.success.call_count, 2)

    def test_keyboard_cart_focus_survives_quantity_edit(self):
        self.make_order()
        self.app.cart.selection_set("lychee")
        self.app.cart.focus("lychee")
        self.app.cart_buttons[0].invoke()
        self.assertEqual(self.app.cart.selection(), ("lychee",))
        self.assertEqual(self.app.cart.focus(), "lychee")
        self.root.focus_force()
        self.app.cart.focus_set()
        self.root.update()
        self.app.cart.event_generate("<Down>")
        self.root.update()
        self.assertEqual(self.app.cart.selection(), ("water",))

    def test_controls_fit_minimum_window(self):
        self.root.geometry("900x600")
        self.root.update()
        for widget in (self.app.cart, self.app.cash_entry, self.app.confirm_button,
                       self.app.receipt, *self.app.product_buttons, *self.app.cart_buttons):
            with self.subTest(widget=widget):
                right = widget.winfo_rootx() - self.root.winfo_rootx() + widget.winfo_width()
                bottom = widget.winfo_rooty() - self.root.winfo_rooty() + widget.winfo_height()
                self.assertLessEqual(right, self.root.winfo_width())
                self.assertLessEqual(bottom, self.root.winfo_height())


if __name__ == "__main__":
    unittest.main()

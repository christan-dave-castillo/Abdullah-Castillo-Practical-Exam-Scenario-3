"""Desktop interface for the Scenario 3 milk tea POS."""

import sys
import tkinter as tk
from tkinter import messagebox, ttk

from pos_logic import POS, POSError, PRODUCTS, money


class POSApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Milk Tea and Beverage Shop POS")
        root.geometry("1000x680")
        root.minsize(900, 600)
        self.pos = POS()
        self.cash = tk.StringVar()
        self.total = tk.StringVar(value="Total: ₱0.00")
        self.change = tk.StringVar(value="Change: —")
        self.status = tk.StringVar(value="Browse products to begin a transaction.")
        self.product_buttons = []
        self._build_interface()
        self.cash.trace_add("write", self._cash_changed)
        self.cash_entry.bind("<Return>", lambda event: self.validate_payment())
        self._refresh()

    def _build_interface(self):
        page = ttk.Frame(self.root, padding=12)
        page.pack(fill="both", expand=True)
        page.columnconfigure(1, weight=1)
        page.rowconfigure(1, weight=1)
        page.rowconfigure(2, weight=1)
        ttk.Label(page, text="Milk Tea and Beverage Shop", font=("Arial", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        products = ttk.LabelFrame(page, text="1. Browse / 2. Add to cart", padding=10)
        products.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        products.columnconfigure(0, weight=1)
        for row, product in enumerate(PRODUCTS):
            button = ttk.Button(
                products, text=f"{product.name}\n₱{product.price:.2f}",
                command=lambda item_id=product.id: self.add_product(item_id),
            )
            button.grid(row=row, column=0, sticky="ew", pady=5, ipady=8)
            self.product_buttons.append(button)

        order = ttk.LabelFrame(page, text="3. Review order", padding=10)
        order.grid(row=1, column=1, sticky="nsew")
        order.columnconfigure(0, weight=1)
        order.rowconfigure(0, weight=1)
        columns = ("name", "quantity", "price", "subtotal")
        self.cart = ttk.Treeview(order, columns=columns, show="headings", selectmode="browse", height=7)
        for key, title, width in (
            ("name", "Item", 245), ("quantity", "Qty", 45),
            ("price", "Unit price", 85), ("subtotal", "Subtotal", 85),
        ):
            self.cart.heading(key, text=title)
            self.cart.column(
                key, width=width, minwidth=width,
                stretch=key == "name", anchor="w" if key == "name" else "e",
            )
        self.cart.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(order, orient="vertical", command=self.cart.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.cart.configure(yscrollcommand=scroll.set)
        controls = ttk.Frame(order)
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.cart_buttons = []
        for text, action in (("+ Quantity", "increase"), ("− Quantity", "decrease"), ("Remove", "remove")):
            button = ttk.Button(controls, text=text, command=lambda name=action: self.edit_cart(name))
            button.pack(side="left", padx=(0, 6))
            self.cart_buttons.append(button)
        ttk.Label(controls, textvariable=self.total, font=("Arial", 12, "bold")).pack(side="right")

        checkout = ttk.Frame(page)
        checkout.grid(row=2, column=1, sticky="nsew", pady=(12, 0))
        checkout.columnconfigure(1, weight=1)
        checkout.rowconfigure(0, weight=1)
        payment = ttk.LabelFrame(checkout, text="4–6. Cash payment", padding=10)
        payment.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        ttk.Label(payment, text="Cash paid (₱):").pack(anchor="w")
        self.cash_entry = ttk.Entry(payment, textvariable=self.cash, width=20)
        self.cash_entry.pack(fill="x", pady=(4, 10))
        self.validate_button = ttk.Button(payment, text="Validate & Compute", command=self.validate_payment)
        self.validate_button.pack(fill="x")
        ttk.Label(payment, textvariable=self.change).pack(anchor="w", pady=10)
        self.confirm_button = ttk.Button(payment, text="Confirm Payment", command=self.confirm_payment, state="disabled")
        self.confirm_button.pack(fill="x")
        ttk.Button(payment, text="New Transaction", command=self.new_transaction).pack(fill="x", pady=(16, 0))

        receipt_panel = ttk.LabelFrame(checkout, text="7. Digital receipt", padding=10)
        receipt_panel.grid(row=0, column=1, sticky="nsew")
        receipt_panel.columnconfigure(0, weight=1)
        receipt_panel.rowconfigure(0, weight=1)
        self.receipt = tk.Text(receipt_panel, width=38, height=13, wrap="word", state="disabled")
        self.receipt.grid(row=0, column=0, sticky="nsew")
        receipt_scroll = ttk.Scrollbar(receipt_panel, command=self.receipt.yview)
        receipt_scroll.grid(row=0, column=1, sticky="ns")
        self.receipt.configure(yscrollcommand=receipt_scroll.set)
        ttk.Label(page, textvariable=self.status, wraplength=850).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

    def add_product(self, product_id):
        try:
            self.pos.add(product_id)
        except POSError as error:
            self._show_error(error)
            return
        self._refresh()
        self.cart.selection_set(product_id)
        self.cart.focus(product_id)
        self.cart.see(product_id)
        self.status.set("Item added. Review the order, then validate the cash payment.")

    def edit_cart(self, action):
        selected = self.cart.selection()
        if not selected:
            self._show_error(POSError("Select a cart item first."))
            return
        try:
            if action == "increase":
                self.pos.increase(selected[0])
            elif action == "decrease":
                self.pos.decrease(selected[0])
            elif action == "remove":
                self.pos.remove(selected[0])
        except POSError as error:
            self._show_error(error)
            return
        self._refresh()
        self.status.set("Cart updated. Validate the payment again before confirming.")

    def _cash_changed(self, *_):
        try:
            self.pos.set_cash(self.cash.get())
        except POSError as error:
            self._show_error(error)
            return
        self._refresh_payment()
        self.status.set("Cash changed. Use Validate & Compute before confirming.")

    def validate_payment(self):
        try:
            change = self.pos.validate_payment()
        except POSError as error:
            self._refresh_payment()
            self._show_error(error)
            return
        self._refresh_payment()
        self.status.set(f"Payment validated. Change: {money(change)}. Ready to confirm.")

    def confirm_payment(self):
        if self.pos.confirmed or self.pos.validated_cash is None:
            self._show_error(POSError("Validate an unpaid transaction before confirming."))
            return
        details = "\n".join(
            f"{item.quantity} × {item.product.name}: {money(item.subtotal)}"
            for item in self.pos.items
        )
        details += (
            f"\n\nTotal: {money(self.pos.total)}"
            f"\nCash paid: {money(self.pos.validated_cash)}"
            f"\nChange: {money(self.pos.change)}\n\nConfirm this payment?"
        )
        if not messagebox.askyesno("Confirm payment", details, parent=self.root):
            self.status.set("Payment not confirmed. You can review or change the order.")
            return
        try:
            self.pos.confirm_payment()
        except POSError as error:
            self._show_error(error)
            return
        self._refresh()
        self.status.set(f"Payment successful — {self.pos.reference}. Start a New Transaction for the next order.")
        messagebox.showinfo(
            "Payment successful",
            f"Transaction {self.pos.reference}\nChange: {money(self.pos.change)}\nYour receipt is displayed.",
            parent=self.root,
        )

    def new_transaction(self):
        self.pos.new_transaction()
        self.cash.set("")
        self._refresh()
        self.status.set("Browse products to begin a transaction.")
        self.product_buttons[0].focus_set()

    def _refresh(self):
        selected = self.cart.selection()
        focused = self.cart.focus()
        rows = self.cart.get_children()
        if rows:
            self.cart.delete(*rows)
        for item in self.pos.items:
            self.cart.insert("", "end", iid=item.product.id, values=(
                item.product.name, item.quantity, money(item.product.price), money(item.subtotal),
            ))
        if selected and self.cart.exists(selected[0]):
            self.cart.selection_set(selected[0])
        # Rebuilding rows clears Treeview's keyboard focus as well as selection.
        if focused and self.cart.exists(focused):
            self.cart.focus(focused)
        self.total.set(f"Total: {money(self.pos.total)}")
        state = "disabled" if self.pos.confirmed else "normal"
        for button in self.product_buttons + self.cart_buttons:
            button.configure(state=state)
        self.receipt.configure(state="normal")
        self.receipt.delete("1.0", "end")
        self.receipt.insert("1.0", self.pos.receipt)
        self.receipt.configure(state="disabled")
        self._refresh_payment()

    def _refresh_payment(self):
        change = self.pos.change
        self.change.set(f"Change: {money(change)}" if change is not None else "Change: —")
        self.cash_entry.configure(state="disabled" if self.pos.confirmed else "normal")
        self.validate_button.configure(state="disabled" if self.pos.confirmed else "normal")
        can_confirm = self.pos.validated_cash is not None and not self.pos.confirmed
        self.confirm_button.configure(state="normal" if can_confirm else "disabled")

    def _show_error(self, error):
        self.status.set(str(error))
        messagebox.showerror("Please check the transaction", str(error), parent=self.root)


if __name__ == "__main__":
    try:
        window = tk.Tk()
    except tk.TclError as error:
        print(f"Cannot open the Tkinter window: {error}", file=sys.stderr)
        print("Run on a desktop with Tkinter and an active display. Headless tests: python -m unittest discover -s tests -v", file=sys.stderr)
        sys.exit(1)
    POSApp(window)
    window.mainloop()

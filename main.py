"""Desktop interface for the Scenario 3 milk tea POS."""

import tkinter as tk
from tkinter import ttk

from pos_logic import PRODUCTS


class POSApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Milk Tea and Beverage Shop POS")
        root.geometry("1000x680")
        root.minsize(900, 600)
        self.cash = tk.StringVar()
        self.total = tk.StringVar(value="Total: ₱0.00")
        self.change = tk.StringVar(value="Change: —")
        self.status = tk.StringVar(value="Browse products to begin a transaction.")
        self.product_buttons = []
        self._build_interface()

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
            self.cart.column(key, width=width, minwidth=width, anchor="w" if key == "name" else "e")
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

    # Transaction behavior is added in the next implementation commit.
    def add_product(self, product_id):
        self.status.set("Product controls are ready for transaction logic.")

    def edit_cart(self, action):
        self.status.set("Select a cart item to adjust its quantity or remove it.")

    def validate_payment(self):
        self.status.set("Payment controls are ready for validation logic.")

    def confirm_payment(self):
        pass

    def new_transaction(self):
        self.cash.set("")
        self.status.set("Browse products to begin a transaction.")


if __name__ == "__main__":
    window = tk.Tk()
    POSApp(window)
    window.mainloop()

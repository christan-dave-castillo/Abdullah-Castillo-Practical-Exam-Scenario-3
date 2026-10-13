"""In-memory POS logic, independent of Tkinter so it can be tested headlessly."""

import re
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    price: Decimal


PRODUCTS = (
    Product("classic", "Classic Milk Tea (Regular)", Decimal("59.00")),
    Product("wintermelon", "Wintermelon Milk Tea (Regular)", Decimal("65.00")),
    Product("taro", "Taro Milk Tea (Regular)", Decimal("65.00")),
    Product("lychee", "Fruit Tea — Lychee (Regular)", Decimal("55.00")),
    Product("brown_sugar", "Brown Sugar Milk Tea (Regular)", Decimal("69.00")),
    Product("water", "Bottled Water", Decimal("20.00")),
)


def money(amount: Decimal) -> str:
    return f"₱{amount:,.2f}"


class POSError(ValueError):
    """An expected input or transaction error suitable for an on-screen alert."""


@dataclass(frozen=True)
class CartItem:
    product: Product
    quantity: int

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity


class POS:
    def __init__(self):
        self.new_transaction()

    def new_transaction(self):
        self._cart: dict[str, int] = {}
        self._cash_text = ""
        self._validated_cash: Decimal | None = None
        self._confirmed = False
        self._reference = ""
        self._receipt = ""

    @property
    def items(self) -> tuple[CartItem, ...]:
        return tuple(CartItem(self._product(key), qty) for key, qty in self._cart.items())

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0.00"))

    @property
    def cash_text(self) -> str:
        return self._cash_text

    @property
    def validated_cash(self) -> Decimal | None:
        return self._validated_cash

    @property
    def change(self) -> Decimal | None:
        if self._validated_cash is None:
            return None
        return self._validated_cash - self.total

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    @property
    def reference(self) -> str:
        return self._reference

    @property
    def receipt(self) -> str:
        return self._receipt

    def _ensure_open(self):
        if self._confirmed:
            raise POSError("Payment is already confirmed. Start a New Transaction.")

    def _product(self, product_id: str) -> Product:
        for product in PRODUCTS:
            if product.id == product_id:
                return product
        raise POSError("Unknown product. Choose one of the six listed products.")

    def _require_item(self, product_id: str):
        self._ensure_open()
        if product_id not in self._cart:
            raise POSError("Select an item that is in the cart.")

    def add(self, product_id: str):
        self._ensure_open()
        self._product(product_id)
        self._cart[product_id] = self._cart.get(product_id, 0) + 1
        self._validated_cash = None

    def increase(self, product_id: str):
        self._require_item(product_id)
        self.add(product_id)

    def decrease(self, product_id: str):
        self._require_item(product_id)
        if self._cart[product_id] == 1:
            del self._cart[product_id]
        else:
            self._cart[product_id] -= 1
        self._validated_cash = None

    def remove(self, product_id: str):
        self._require_item(product_id)
        del self._cart[product_id]
        self._validated_cash = None

    def set_cash(self, text: str):
        self._ensure_open()
        if text != self._cash_text:
            self._cash_text = text
            self._validated_cash = None

    def validate_payment(self) -> Decimal:
        self._ensure_open()
        # A failed validation must never leave an earlier valid payment active.
        self._validated_cash = None
        if not self._cart:
            raise POSError("Add at least one product before entering payment.")
        text = self._cash_text.strip()
        if not text:
            raise POSError("Cash is blank. Please enter a cash amount.")
        if len(text) > 16:
            raise POSError("Cash amount is too long (maximum 16 characters).")
        if re.fullmatch(r"-[0-9]+(?:\.[0-9]+)?", text):
            raise POSError("Cash cannot be negative. Enter a non-negative amount.")
        # Reject NaN, Infinity, exponents, code, and more than two decimal places.
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text):
            raise POSError("Cash must be numeric, using digits and up to two decimal places.")
        cash = Decimal(text).quantize(Decimal("0.01"))
        if cash < self.total:
            raise POSError(f"Insufficient payment. Please enter at least {money(self.total)}.")
        self._validated_cash = cash
        return cash - self.total

    def confirm_payment(self) -> str:
        self._ensure_open()
        if self._validated_cash is None:
            raise POSError("Validate the current cart and cash before confirming payment.")
        self._reference = f"MT-{uuid4().hex[:12].upper()}"
        lines = ["MILK TEA AND BEVERAGE SHOP", f"Transaction: {self._reference}", ""]
        for item in self.items:
            lines.extend([
                item.product.name,
                f"  Qty {item.quantity} × {money(item.product.price)} = {money(item.subtotal)}",
            ])
        lines.extend([
            "", f"TOTAL: {money(self.total)}", f"Cash paid: {money(self._validated_cash)}",
            f"Change: {money(self.change)}", "", "Payment confirmed. Thank you!",
        ])
        self._receipt = "\n".join(lines)
        self._confirmed = True
        return self._receipt

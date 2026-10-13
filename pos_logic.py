"""Products and money formatting for the milk tea POS."""

from dataclasses import dataclass
from decimal import Decimal


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

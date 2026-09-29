"""他社単価から自社単価を決める."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from .reader import LineItem


@dataclass
class PricingRule:
    rate: float = 0.95  # 他社単価に掛ける率 (0.95 = 5% 安く)
    round_unit: int = 10  # 丸め単位 (円)
    round_mode: str = "down"  # down / up / nearest

    def apply(self, price: float) -> int:
        value = price * self.rate
        unit = max(1, self.round_unit)
        if self.round_mode == "up":
            return int(math.ceil(value / unit - 1e-9) * unit)
        if self.round_mode == "nearest":
            return int(math.floor(value / unit + 0.5) * unit)
        return int(math.floor(value / unit + 1e-9) * unit)


@dataclass
class PricedItem:
    item: LineItem
    competitor_price: float

    @property
    def diff(self) -> float:
        return self.item.unit_price - self.competitor_price


def price_items(items: list[LineItem], rule: PricingRule) -> list[PricedItem]:
    return [
        PricedItem(item=replace(it, unit_price=rule.apply(it.unit_price)), competitor_price=it.unit_price)
        for it in items
    ]

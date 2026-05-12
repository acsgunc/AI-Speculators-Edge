"""Domain models — pure data containers with no framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PriceTier:
    percentage: int
    target_price: float


@dataclass(frozen=True, slots=True)
class AverageDownRow:
    target_avg_price: float
    units_to_buy: float
    total_cost: float
    new_position_value: float


@dataclass(frozen=True, slots=True)
class PositionInput:
    entry_price: float
    current_qty: int
    market_price: float

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.entry_price <= 0:
            errors.append("Entry Price must be greater than zero.")
        if self.current_qty <= 0:
            errors.append("Current Quantity must be at least 1.")
        if self.market_price <= 0:
            errors.append("Current Market Price must be greater than zero.")
        if self.market_price >= self.entry_price:
            errors.append(
                "Current Market Price should be below your Entry Price for averaging down."
            )
        return errors

    @property
    def total_cost_basis(self) -> float:
        return self.entry_price * self.current_qty

    @property
    def unrealised_pnl_pct(self) -> float:
        return round(
            (self.market_price - self.entry_price) / self.entry_price * 100, 1
        )

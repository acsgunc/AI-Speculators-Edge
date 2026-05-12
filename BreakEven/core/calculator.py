"""Pure calculation engine — no I/O, no UI, fully testable."""

from __future__ import annotations

from .models import AverageDownRow, PositionInput, PriceTier

PCT_RANGE = range(-100, 505, 5)
DEFAULT_TARGETS = [250, 200, 150, 100, 75]
DYNAMIC_STEPS = 8


def compute_price_tiers(base_price: float) -> list[PriceTier]:
    return [
        PriceTier(
            percentage=pct,
            target_price=round(base_price * (1 + pct / 100), 2),
        )
        for pct in PCT_RANGE
    ]


def _resolve_targets(pos: PositionInput) -> list[float]:
    targets = sorted(
        {t for t in DEFAULT_TARGETS if pos.market_price < t < pos.entry_price},
        reverse=True,
    )
    if len(targets) >= 3:
        return targets

    step = max(1, round((pos.entry_price - pos.market_price) / DYNAMIC_STEPS, 2))
    return sorted(
        {
            round(pos.market_price + i * step, 2)
            for i in range(1, DYNAMIC_STEPS)
            if pos.market_price < pos.market_price + i * step < pos.entry_price
        },
        reverse=True,
    )


def compute_average_down(pos: PositionInput) -> list[AverageDownRow]:
    rows: list[AverageDownRow] = []
    for target_avg in _resolve_targets(pos):
        denom = target_avg - pos.market_price
        if denom <= 0:
            continue
        units = (pos.total_cost_basis - target_avg * pos.current_qty) / denom
        if units <= 0:
            continue
        units = round(units, 2)
        cost = round(units * pos.market_price, 2)
        new_qty = pos.current_qty + units
        rows.append(
            AverageDownRow(
                target_avg_price=target_avg,
                units_to_buy=units,
                total_cost=cost,
                new_position_value=round(new_qty * pos.market_price, 2),
            )
        )
    return rows

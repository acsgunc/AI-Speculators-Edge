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


def _resolve_targets(
    pos: PositionInput,
    step_size: float | None = None,
    step_pct: float | None = None,
) -> list[float]:
    # Percentage-based stepping: compound from market price upward
    # e.g. market=60, 10% → 66, 72.6, 79.86, … until entry price
    if step_pct is not None and step_pct > 0:
        targets: list[float] = []
        multiplier = 1 + step_pct / 100
        price = round(pos.market_price * multiplier, 2)
        while price < pos.entry_price:
            targets.append(price)
            price = round(price * multiplier, 2)
        return sorted(targets, reverse=True)

    # Absolute-value stepping
    if step_size is not None and step_size > 0:
        targets = []
        price = step_size
        while price < pos.entry_price:
            if price > pos.market_price:
                targets.append(round(price, 2))
            price = round(price + step_size, 10)
        return sorted(targets, reverse=True)

    defaults = sorted(
        {t for t in DEFAULT_TARGETS if pos.market_price < t < pos.entry_price},
        reverse=True,
    )
    if len(defaults) >= 3:
        return defaults

    step = max(1, round((pos.entry_price - pos.market_price) / DYNAMIC_STEPS, 2))
    return sorted(
        {
            round(pos.market_price + i * step, 2)
            for i in range(1, DYNAMIC_STEPS)
            if pos.market_price < pos.market_price + i * step < pos.entry_price
        },
        reverse=True,
    )


def compute_average_down(
    pos: PositionInput,
    step_size: float | None = None,
    step_pct: float | None = None,
) -> list[AverageDownRow]:
    rows: list[AverageDownRow] = []
    for target_avg in _resolve_targets(pos, step_size, step_pct):
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

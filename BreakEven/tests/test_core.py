"""Unit tests for core domain logic — models, calculator, export."""

import math

import pandas as pd
import pytest

from core.calculator import compute_average_down, compute_price_tiers
from core.export import avg_down_to_dataframe, combined_csv, tiers_to_dataframe
from core.models import AverageDownRow, PositionInput, PriceTier


# ═══════════════════════════════════════════════════════════════════════════════
# models.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestPriceTier:
    def test_immutable(self):
        t = PriceTier(percentage=10, target_price=110.0)
        with pytest.raises(AttributeError):
            t.percentage = 20  # type: ignore[misc]

    def test_fields(self):
        t = PriceTier(percentage=-5, target_price=95.0)
        assert t.percentage == -5
        assert t.target_price == 95.0


class TestPositionInput:
    def test_valid_input_no_errors(self):
        p = PositionInput(entry_price=300, current_qty=2, market_price=50)
        assert p.validate() == []

    def test_zero_entry_price(self):
        p = PositionInput(entry_price=0, current_qty=2, market_price=50)
        errors = p.validate()
        assert any("Entry Price" in e for e in errors)

    def test_zero_quantity(self):
        p = PositionInput(entry_price=300, current_qty=0, market_price=50)
        errors = p.validate()
        assert any("Quantity" in e for e in errors)

    def test_zero_market_price(self):
        p = PositionInput(entry_price=300, current_qty=2, market_price=0)
        errors = p.validate()
        assert any("Market Price" in e for e in errors)

    def test_market_above_entry(self):
        p = PositionInput(entry_price=100, current_qty=2, market_price=150)
        errors = p.validate()
        assert any("below" in e.lower() for e in errors)

    def test_market_equals_entry(self):
        p = PositionInput(entry_price=100, current_qty=2, market_price=100)
        errors = p.validate()
        assert len(errors) > 0

    def test_total_cost_basis(self):
        p = PositionInput(entry_price=300, current_qty=2, market_price=50)
        assert p.total_cost_basis == 600

    def test_unrealised_pnl_pct(self):
        p = PositionInput(entry_price=300, current_qty=2, market_price=50)
        assert p.unrealised_pnl_pct == -83.3

    def test_unrealised_pnl_value(self):
        p = PositionInput(entry_price=300, current_qty=2, market_price=50)
        assert p.unrealised_pnl_value == -500.0

    def test_unrealised_pnl_value_single_unit(self):
        p = PositionInput(entry_price=100, current_qty=1, market_price=80)
        assert p.unrealised_pnl_value == -20.0


# ═══════════════════════════════════════════════════════════════════════════════
# calculator.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputePriceTiers:
    def test_returns_121_tiers(self):
        # -100 to +500 in 5% steps = 121 entries
        tiers = compute_price_tiers(100)
        assert len(tiers) == 121

    def test_zero_pct_equals_base(self):
        tiers = compute_price_tiers(200)
        zero = [t for t in tiers if t.percentage == 0]
        assert len(zero) == 1
        assert zero[0].target_price == 200.0

    def test_minus_100_is_zero(self):
        tiers = compute_price_tiers(100)
        bottom = [t for t in tiers if t.percentage == -100]
        assert bottom[0].target_price == 0.0

    def test_plus_100_is_double(self):
        tiers = compute_price_tiers(50)
        double = [t for t in tiers if t.percentage == 100]
        assert double[0].target_price == 100.0

    def test_plus_500_is_six_times(self):
        tiers = compute_price_tiers(10)
        top = [t for t in tiers if t.percentage == 500]
        assert top[0].target_price == 60.0

    def test_calculation_formula(self):
        base = 123.45
        tiers = compute_price_tiers(base)
        for t in tiers:
            expected = round(base * (1 + t.percentage / 100), 2)
            assert t.target_price == expected


class TestComputeAverageDown:
    def test_auto_mode_returns_rows(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        assert len(rows) > 0
        assert all(isinstance(r, AverageDownRow) for r in rows)

    def test_all_targets_between_market_and_entry(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        for r in rows:
            assert r.target_avg_price > pos.market_price
            assert r.target_avg_price < pos.entry_price

    def test_units_positive(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        for r in rows:
            assert r.units_to_buy > 0

    def test_total_cost_equals_units_times_market(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        for r in rows:
            expected = round(r.units_to_buy * pos.market_price, 2)
            assert r.total_cost == expected

    def test_dca_formula_correctness(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        for r in rows:
            new_avg = (pos.total_cost_basis + r.units_to_buy * pos.market_price) / (
                pos.current_qty + r.units_to_buy
            )
            assert abs(new_avg - r.target_avg_price) < 0.5

    def test_step_size_dollar(self):
        pos = PositionInput(10, 2, 6)
        rows = compute_average_down(pos, step_size=1)
        targets = [r.target_avg_price for r in rows]
        assert 7 in targets
        assert 8 in targets
        assert 9 in targets

    def test_step_size_dollar_skip_below_market(self):
        pos = PositionInput(10, 2, 6)
        rows = compute_average_down(pos, step_size=1)
        for r in rows:
            assert r.target_avg_price > 6

    def test_step_size_dollar_step2(self):
        pos = PositionInput(10, 2, 6)
        rows = compute_average_down(pos, step_size=2)
        targets = [r.target_avg_price for r in rows]
        assert 8 in targets
        assert 7 not in targets

    def test_step_size_fraction(self):
        pos = PositionInput(10, 2, 6)
        rows = compute_average_down(pos, step_size=0.5)
        targets = [r.target_avg_price for r in rows]
        assert 6.5 in targets
        assert 7.0 in targets
        assert 9.5 in targets

    def test_step_pct_1_percent(self):
        pos = PositionInput(100, 2, 60)
        rows = compute_average_down(pos, step_pct=1)
        targets = [r.target_avg_price for r in rows]
        # 61% of 100 = 61, 99% = 99 — all integers from 61..99
        assert 61 in targets
        assert 99 in targets
        assert len(targets) == 39  # 61..99

    def test_step_pct_5_percent(self):
        pos = PositionInput(200, 2, 50)
        rows = compute_average_down(pos, step_pct=5)
        targets = [r.target_avg_price for r in rows]
        # 5%=10, 10%=20, ..., 95%=190 — only those > 50
        expected = [round(200 * p / 100, 2) for p in range(5, 100, 5) if 200 * p / 100 > 50]
        assert targets == sorted(expected, reverse=True)

    def test_step_pct_fractional(self):
        pos = PositionInput(100, 2, 95)
        rows = compute_average_down(pos, step_pct=0.5)
        targets = [r.target_avg_price for r in rows]
        assert 95.5 in targets
        assert 96.0 in targets
        assert 99.5 in targets

    def test_step_pct_overrides_step_size(self):
        pos = PositionInput(300, 2, 50)
        rows_pct = compute_average_down(pos, step_pct=10)
        rows_dollar = compute_average_down(pos, step_size=25)
        # They should produce different target lists
        t_pct = [r.target_avg_price for r in rows_pct]
        t_dollar = [r.target_avg_price for r in rows_dollar]
        assert t_pct != t_dollar

    def test_empty_when_no_valid_targets(self):
        pos = PositionInput(10, 2, 9.5)
        rows = compute_average_down(pos, step_size=5)
        assert rows == []


# ═══════════════════════════════════════════════════════════════════════════════
# export.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestExport:
    def test_tiers_to_dataframe_shape(self):
        tiers = compute_price_tiers(100)
        df = tiers_to_dataframe(tiers)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 121
        assert "Percentage Change (%)" in df.columns
        assert "Target Price ($)" in df.columns

    def test_avg_down_to_dataframe(self):
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        df = avg_down_to_dataframe(rows)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(rows)
        assert "Target Avg Price ($)" in df.columns
        assert "Units to Buy Now" in df.columns

    def test_combined_csv_tiers_only(self):
        tiers = compute_price_tiers(100)
        df = tiers_to_dataframe(tiers)
        csv = combined_csv(df)
        assert "=== PRICE TIERS ===" in csv
        assert "=== AVERAGE DOWN ===" not in csv

    def test_combined_csv_with_avg(self):
        tiers = compute_price_tiers(100)
        tier_df = tiers_to_dataframe(tiers)
        pos = PositionInput(300, 2, 50)
        rows = compute_average_down(pos)
        avg_df = avg_down_to_dataframe(rows)
        csv = combined_csv(tier_df, avg_df)
        assert "=== PRICE TIERS ===" in csv
        assert "=== AVERAGE DOWN ===" in csv

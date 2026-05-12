"""Position-repair section — inputs, validation, metric cards, table."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.calculator import compute_average_down
from core.export import avg_down_to_dataframe
from core.models import PositionInput
from ui.theme import COLOR_DANGER


def render(ticker_name: str) -> tuple[pd.DataFrame | None, list[str]]:
    st.header("🛠️ Position Repair — Average Down Calculator")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        entry_price = st.number_input(
            "Entry Price ($)", min_value=0.01, value=300.0, step=0.01, format="%.2f"
        )
    with c2:
        current_qty = st.number_input(
            "Current Quantity", min_value=1, value=2, step=1
        )
    with c3:
        market_price = st.number_input(
            "Current Market Price ($)",
            min_value=0.01,
            value=50.0,
            step=0.01,
            format="%.2f",
        )
    with c4:
        step_mode = st.radio(
            "Step Mode",
            ["Auto", "Dollar ($)", "Percent (%)"],
            horizontal=True,
            help="Choose how target average prices are spaced.",
        )
        step_size = None
        step_pct = None
        if step_mode == "Dollar ($)":
            raw = st.number_input(
                "Step Size ($)",
                min_value=0.01,
                value=25.0,
                step=0.5,
                format="%.2f",
            )
            step_size = raw
        elif step_mode == "Percent (%)":
            raw = st.number_input(
                "Step Size (%)",
                min_value=0.01,
                value=1.0,
                step=0.5,
                format="%.2f",
            )
            step_pct = raw

    pos = PositionInput(
        entry_price=entry_price,
        current_qty=current_qty,
        market_price=market_price,
    )
    errors = pos.validate()

    if errors:
        for e in errors:
            st.error(e)
        return None, errors

    rows = compute_average_down(pos, step_size=step_size, step_pct=step_pct)
    if not rows:
        st.info(
            "No valid average-down targets could be computed with the current inputs. "
            "Try adjusting the Entry Price or Market Price."
        )
        return None, []

    avg_df = avg_down_to_dataframe(rows)

    _render_metrics(pos)
    st.markdown("")
    st.dataframe(avg_df, use_container_width=True, hide_index=True)

    st.download_button(
        label="⬇️  Download Average-Down CSV",
        data=avg_df.to_csv(index=False),
        file_name=f"average_down_{ticker_name}.csv",
        mime="text/csv",
        key="avg_csv",
    )
    return avg_df, []


def _render_metrics(pos: PositionInput) -> None:
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        _card(f"${pos.entry_price:,.2f}", "Original Entry")
    with m2:
        _card(f"${pos.market_price:,.2f}", "Current Market")
    with m3:
        _card(
            f"{pos.unrealised_pnl_pct}%",
            "Unrealised P&L (%)",
            value_color=COLOR_DANGER,
        )
    with m4:
        _card(
            f"${pos.unrealised_pnl_value:,.2f}",
            "Unrealised P&L ($)",
            value_color=COLOR_DANGER,
        )


def _card(value: str, label: str, value_color: str | None = None) -> None:
    style = f' style="color:{value_color}"' if value_color else ""
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-value"{style}>{value}</div>'
        f'<div class="metric-label">{label}</div></div>',
        unsafe_allow_html=True,
    )

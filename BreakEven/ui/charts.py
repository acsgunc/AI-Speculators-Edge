"""Price-tier table (HTML) and Plotly chart renderers."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui.theme import (
    COLOR_ACCENT,
    COLOR_BG,
    COLOR_GOLD,
    COLOR_GRID,
    COLOR_TEXT,
)


# ── HTML Table ──────────────────────────────────────────────────────────────────

def render_tier_table(df: pd.DataFrame) -> None:
    rows: list[str] = []
    for _, r in df.iterrows():
        pct = int(r["Percentage Change (%)"])
        price = r["Target Price ($)"]
        if pct == 0:
            css = "anchor-row"
            cell = f'<span style="font-weight:700">► {pct}% (Current)</span>'
        elif pct > 0:
            css = ""
            cell = f'<span class="success-text">+{pct}%</span>'
        else:
            css = ""
            cell = f'<span class="danger-text">{pct}%</span>'
        rows.append(
            f'<tr class="{css}">'
            f'<td style="padding:6px 14px">{cell}</td>'
            f'<td style="padding:6px 14px;text-align:right">${price:,.2f}</td>'
            f"</tr>"
        )

    header = (
        "<thead><tr>"
        '<th style="padding:8px 14px;text-align:left">Change</th>'
        '<th style="padding:8px 14px;text-align:right">Target Price</th>'
        "</tr></thead>"
    )
    html = (
        '<div style="max-height:500px;overflow-y:auto">'
        '<table style="width:100%;border-collapse:collapse;font-size:14px">'
        f"{header}<tbody>{''.join(rows)}</tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# ── Plotly Chart ────────────────────────────────────────────────────────────────

def render_price_chart(
    df: pd.DataFrame,
    base_price: float,
    ticker_name: str,
) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Percentage Change (%)"],
            y=df["Target Price ($)"],
            mode="lines+markers",
            marker=dict(size=4, color=COLOR_ACCENT),
            line=dict(width=2, color=COLOR_ACCENT),
            name="Target Price",
        )
    )
    fig.add_hline(
        y=base_price,
        line_dash="dash",
        line_color=COLOR_GOLD,
        annotation_text=f"Current ${base_price:,.2f}",
        annotation_position="top left",
        annotation_font=dict(color=COLOR_GOLD, size=12),
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLOR_BG,
        plot_bgcolor=COLOR_BG,
        title=dict(
            text=f"Price Targets — {ticker_name}",
            font=dict(size=18, color=COLOR_TEXT),
        ),
        xaxis=dict(
            title="Percentage Change (%)",
            gridcolor=COLOR_GRID,
            zeroline=True,
            zerolinecolor=COLOR_GOLD,
            zerolinewidth=1,
        ),
        yaxis=dict(
            title="Target Price ($)",
            gridcolor=COLOR_GRID,
            tickprefix="$",
        ),
        margin=dict(l=60, r=30, t=50, b=50),
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)

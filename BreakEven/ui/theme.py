"""Shared UI constants and CSS injection."""

import streamlit as st

# ── Colour Palette ──────────────────────────────────────────────────────────────
COLOR_BG = "#0e1117"
COLOR_BG_SECONDARY = "#1a1f2e"
COLOR_GRID = "#1e293b"
COLOR_ACCENT = "#00d4aa"
COLOR_SUCCESS = "#00d47e"
COLOR_DANGER = "#ff4b4b"
COLOR_GOLD = "#ffd700"
COLOR_TEXT = "#fafafa"
COLOR_MUTED = "#a0aec0"
COLOR_BORDER = "#2d3748"


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        .main, .stApp {{ background-color: {COLOR_BG}; }}
        h1, h2, h3 {{ color: {COLOR_TEXT}; }}
        .success-text {{ color: {COLOR_SUCCESS}; font-weight: 600; }}
        .danger-text  {{ color: {COLOR_DANGER}; font-weight: 600; }}
        .anchor-row   {{ background-color: {COLOR_GRID}; font-weight: 700; }}
        .metric-card {{
            background-color: {COLOR_BG_SECONDARY};
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            border: 1px solid {COLOR_BORDER};
        }}
        .metric-value {{ font-size: 28px; font-weight: 700; color: {COLOR_ACCENT}; }}
        .metric-label {{ font-size: 14px; color: {COLOR_MUTED}; margin-top: 4px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

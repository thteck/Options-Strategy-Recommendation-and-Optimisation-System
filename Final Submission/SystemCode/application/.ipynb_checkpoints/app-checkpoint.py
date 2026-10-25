from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Options Strategy Recommendation",
    layout="wide"
)

st.markdown(
    """
    <style>
    div[data-testid="stAlert"] {
        background-color: #1e293b;
    }

    div[data-testid="stAlert"] p {
        color: #f8fafc !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

PROJECT_ROOT = Path.cwd()
NOTEBOOK6_DIR = PROJECT_ROOT / "outputs" / "notebook_06"
NOTEBOOK7_DIR = PROJECT_ROOT / "outputs" / "notebook_07"


def validate_ticker(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker or not re.fullmatch(r"[A-Z0-9.^=-]{1,15}", ticker):
        raise ValueError("Enter a valid ticker containing up to 15 supported characters.")
    return ticker


def money(value, unavailable: str = "N/A") -> str:
    if value is None:
        return unavailable
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return unavailable


def percent(value, unavailable: str = "N/A") -> str:
    if value is None:
        return unavailable
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return unavailable


@st.cache_data(show_spinner=False)
def load_run(ticker: str, outlook: str) -> dict:
    run_name = f"{ticker}_{outlook}"
    paths = {
        "recommendation": NOTEBOOK7_DIR / f"{run_name}_demo_recommendation.json",
        "trade_legs": NOTEBOOK7_DIR / f"{run_name}_demo_trade_legs.csv",
        "payoff_curve": NOTEBOOK7_DIR / f"{run_name}_demo_payoff_curve.csv",
        "payoff_scenarios": NOTEBOOK7_DIR / f"{run_name}_demo_payoff_scenarios.csv",
        "alternatives": NOTEBOOK7_DIR / f"{run_name}_demo_alternatives.csv",
        "pipeline_status": NOTEBOOK7_DIR / f"{run_name}_demo_pipeline_status.csv",
        "quality_report": NOTEBOOK7_DIR / f"{run_name}_demo_quality_report.csv",
        "method_comparison": NOTEBOOK6_DIR / f"{run_name}_method_comparison.csv",
        "limitations": NOTEBOOK6_DIR / f"{run_name}_evaluation_limitations.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "No completed analysis was found for this ticker/outlook. Run Notebooks 1-7 first. "
            + "Missing: " + ", ".join(missing)
        )
    with paths["recommendation"].open("r", encoding="utf-8") as file:
        payload = json.load(file)
    expected_request = {"ticker": ticker, "outlook": outlook}
    if payload.get("request") != expected_request:
        raise ValueError("Saved recommendation does not match the requested ticker/outlook.")
    return {
        "payload": payload,
        "trade_legs": pd.read_csv(paths["trade_legs"]),
        "payoff_curve": pd.read_csv(paths["payoff_curve"]),
        "payoff_scenarios": pd.read_csv(paths["payoff_scenarios"]),
        "alternatives": pd.read_csv(paths["alternatives"]),
        "pipeline_status": pd.read_csv(paths["pipeline_status"]),
        "quality_report": pd.read_csv(paths["quality_report"]),
        "method_comparison": pd.read_csv(paths["method_comparison"]),
        "limitations": pd.read_csv(paths["limitations"]),
    }


st.title("Options Strategy Recommendation and Optimisation System")
st.caption("Explainable knowledge-based reasoning + constrained genetic-algorithm optimisation")

with st.sidebar:
    st.header("Analysis request")
    ticker_input = st.text_input("Stock ticker", value="AAPL", max_chars=15)
    outlook_input = st.radio("Directional outlook", options=["Bullish", "Bearish"], horizontal=True)
    show_result = st.button("Show recommendation", type="primary", use_container_width=True)
    st.markdown("---")
    st.caption("Required inputs: ticker and outlook only.")

if not show_result:
    st.info("Enter a ticker and outlook, then select **Show recommendation**.")
    st.stop()

try:
    selected_ticker = validate_ticker(ticker_input)
    selected_outlook = outlook_input.lower()
    with st.spinner("Loading the validated recommendation..."):
        run = load_run(selected_ticker, selected_outlook)
except (ValueError, FileNotFoundError, KeyError, json.JSONDecodeError) as error:
    st.error(str(error))
    st.stop()

payload = run["payload"]
market = payload["market"]
recommendation = payload["recommendation"]
evaluation = payload["evaluation"]

st.subheader(f"{selected_ticker} · {selected_outlook.title()} recommendation")
metric_columns = st.columns(5)
metric_columns[0].metric("Strategy", recommendation["strategy_name"])
metric_columns[1].metric("Expiry", recommendation["expiry"])
metric_columns[2].metric("Probability of profit", percent(recommendation["probability_of_profit"]))
metric_columns[3].metric("Expected profit", money(recommendation["adjusted_expected_profit"]))
metric_columns[4].metric("Maximum loss", money(recommendation["adjusted_max_loss"]))

recommendation_tab, payoff_tab, alternatives_tab, evidence_tab, limitations_tab = st.tabs(
    ["Recommendation", "Payoff", "Alternatives", "System evidence", "Limitations"]
)

with recommendation_tab:
    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("### Exact option legs")
        st.dataframe(
            run["trade_legs"],
            hide_index=True,
            use_container_width=True,
            column_config={
                "entry_price_per_share": st.column_config.NumberColumn("Entry price/share", format="$%.2f"),
                "cashflow_per_contract": st.column_config.NumberColumn("Cashflow/contract", format="$%.2f"),
                "strike": st.column_config.NumberColumn("Strike", format="$%.2f"),
            },
        )
        st.markdown("### Why this recommendation")
        st.markdown(f"<div class='decision-note'><b>Strategy family:</b> {recommendation['knowledge_explanation']}</div>", unsafe_allow_html=True)
        st.write("")
        st.markdown(f"<div class='decision-note'><b>Exact contracts:</b> {recommendation['optimisation_explanation']}</div>", unsafe_allow_html=True)
    with right:
        st.markdown("### Market context")
        market_table = pd.DataFrame([
            ("Current price", money(market.get("current_price"))),
            ("Trend", str(market.get("trend_label", "N/A")).replace("_", " ").title()),
            ("Outlook alignment", str(market.get("outlook_alignment", "N/A")).title()),
            ("IV regime", str(market.get("volatility_regime", "N/A")).replace("_", " ").title()),
            ("Expected move", money(market.get("expected_move"))),
            ("Expected range", f"{money(market.get('expected_lower_price'))} to {money(market.get('expected_upper_price'))}"),
        ], columns=["Item", "Value"])
        st.dataframe(market_table, hide_index=True, use_container_width=True)
        st.markdown("### Risk and cost")
        st.write(f"Entry: **{recommendation['entry_type'].title()} {money(recommendation['entry_amount_before_explicit_cost'])}** before explicit cost")
        st.write(f"Estimated transaction cost: **{money(recommendation['estimated_transaction_cost'])}**")
        st.write(f"Expected return on max risk: **{percent(recommendation['net_expected_return_on_risk'])}**")
        st.write(f"Liquidity score: **{float(recommendation['liquidity_score']):.1f}/100**")
        st.write(f"GA fitness: **{float(recommendation['fitness_score']):.2f}/100**")

with payoff_tab:
    st.markdown("### Cost-adjusted expiration payoff")
    payoff = run["payoff_curve"].set_index("terminal_stock_price")[["profit_loss"]]
    st.line_chart(payoff, x_label="Terminal stock price", y_label="Profit / loss (USD)")
    st.markdown("### Expected-move scenarios")
    st.dataframe(
        run["payoff_scenarios"],
        hide_index=True,
        use_container_width=True,
        column_config={
            "terminal_stock_price": st.column_config.NumberColumn("Terminal price", format="$%.2f"),
            "profit_loss": st.column_config.NumberColumn("Profit / loss", format="$%.2f"),
        },
    )
    st.caption("Expiration payoff only; the path before expiry can differ because of volatility, time decay and assignment risk.")

with alternatives_tab:
    st.markdown("### Highest-ranked alternatives")
    alternative_columns = [
        column for column in [
            "fitness_rank", "strategy_name", "expiry", "long_strike", "short_strike",
            "adjusted_expected_profit", "probability_of_profit", "adjusted_max_loss",
            "liquidity_score", "fitness_score",
        ] if column in run["alternatives"].columns
    ]
    st.dataframe(run["alternatives"][alternative_columns], hide_index=True, use_container_width=True)

with evidence_tab:
    st.markdown("### Pipeline readiness")
    st.dataframe(run["pipeline_status"], hide_index=True, use_container_width=True)
    if "pass_rate" in run["pipeline_status"].columns:
        readiness = run["pipeline_status"].set_index("stage")[["pass_rate"]] * 100
        st.bar_chart(readiness, x_label="Pipeline stage", y_label="Checks passed (%)")
    st.markdown("### Quantitative method comparison")
    comparison_columns = [
        column for column in [
            "method", "adjusted_expected_profit", "probability_of_profit",
            "net_expected_return_on_risk", "adjusted_max_loss", "liquidity_score",
            "fitness_score", "stress_expected_profit", "stress_probability_of_profit",
        ] if column in run["method_comparison"].columns
    ]
    st.dataframe(run["method_comparison"][comparison_columns], hide_index=True, use_container_width=True)
    st.write(f"Historical-return stress probability of profit: **{percent(evaluation.get('historical_stress_probability_of_profit'))}**")
    st.write(f"Gap to exhaustive oracle: **{float(evaluation.get('gap_to_exhaustive_oracle') or 0):.4f} fitness points**")

with limitations_tab:
    st.markdown("### Known limitations")
    st.dataframe(run["limitations"], hide_index=True, use_container_width=True)
    st.markdown("<div class='risk-note'><b>Important:</b> The system uses current-chain modelling and historical-underlying stress simulation. It does not claim a full historical-options backtest.</div>", unsafe_allow_html=True)

st.markdown("---")
st.warning(payload["disclaimer"])

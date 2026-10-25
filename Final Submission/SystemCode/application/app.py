"""Interactive, on-demand delivery layer for the recommendation notebooks."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from pipeline import (
    PipelineExecutionError,
    discard_run,
    normalise_outlook,
    normalise_ticker,
    run_pipeline,
)


st.set_page_config(page_title="Options Strategy Recommendation", layout="wide")

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
    unsafe_allow_html=True,
)


def money(value: object, unavailable: str = "N/A") -> str:
    """Format a dollar value without failing the page on incomplete data."""
    try:
        return "$" + f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return unavailable


def percent(value: object, unavailable: str = "N/A") -> str:
    """Format a decimal probability or return without failing the page."""
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return unavailable


def number(value: object, digits: int = 1, unavailable: str = "N/A") -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return unavailable


def _available_columns(frame: pd.DataFrame, candidates: list[str]) -> list[str]:
    return [column for column in candidates if column in frame.columns]


def load_run(run_root: Path, ticker: str, outlook: str) -> dict[str, object]:
    """Load the Notebook 6/7 handoff contract from one temporary run."""
    notebook6_dir = run_root / "outputs" / "notebook_06" / ticker / outlook
    notebook7_dir = run_root / "outputs" / "notebook_07" / ticker / outlook
    paths = {
        "recommendation": notebook7_dir / "demo_recommendation.json",
        "trade_legs": notebook7_dir / "demo_trade_legs.csv",
        "payoff_curve": notebook7_dir / "demo_payoff_curve.csv",
        "payoff_scenarios": notebook7_dir / "demo_payoff_scenarios.csv",
        "alternatives": notebook7_dir / "demo_alternatives.csv",
        "pipeline_status": notebook7_dir / "demo_pipeline_status.csv",
        "quality_report": notebook7_dir / "demo_quality_report.csv",
        "method_comparison": notebook6_dir / "method_comparison.csv",
        "limitations": notebook6_dir / "evaluation_limitations.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "The pipeline finished without all required recommendation files. "
            + "Missing: "
            + ", ".join(missing)
        )

    with paths["recommendation"].open("r", encoding="utf-8") as file:
        payload = json.load(file)

    expected_request = {"ticker": ticker, "outlook": outlook}
    if payload.get("request") != expected_request:
        raise ValueError("The generated recommendation does not match this request.")

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


def render_recommendation(run: dict[str, object]) -> None:
    """Display the validated Notebook 7 recommendation payload."""
    payload = run["payload"]
    assert isinstance(payload, dict)
    market = payload.get("market", {})
    recommendation = payload.get("recommendation", {})
    evaluation = payload.get("evaluation", {})
    request = payload.get("request", {})

    if not isinstance(market, dict):
        market = {}
    if not isinstance(recommendation, dict):
        recommendation = {}
    if not isinstance(evaluation, dict):
        evaluation = {}
    if not isinstance(request, dict):
        request = {}

    ticker = str(request.get("ticker", "Unknown"))
    outlook = str(request.get("outlook", "unknown"))

    st.subheader(f"{ticker} · {outlook.title()} recommendation")
    metric_columns = st.columns(5)
    metric_columns[0].metric("Strategy", str(recommendation.get("strategy_name", "N/A")))
    metric_columns[1].metric("Expiry", str(recommendation.get("expiry", "N/A")))
    metric_columns[2].metric(
        "Probability of profit",
        percent(recommendation.get("probability_of_profit")),
    )
    metric_columns[3].metric(
        "Expected profit",
        money(recommendation.get("adjusted_expected_profit")),
    )
    metric_columns[4].metric(
        "Maximum loss",
        money(recommendation.get("adjusted_max_loss")),
    )

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
                    "entry_price_per_share": st.column_config.NumberColumn(
                        "Entry price/share",
                        format="$%.2f",
                    ),
                    "cashflow_per_contract": st.column_config.NumberColumn(
                        "Cashflow/contract",
                        format="$%.2f",
                    ),
                    "strike": st.column_config.NumberColumn("Strike", format="$%.2f"),
                },
            )
            st.markdown("### Why this recommendation")
            st.markdown(
                "<div class='decision-note'><b>Strategy family:</b> "
                f"{recommendation.get('knowledge_explanation', 'N/A')}</div>",
                unsafe_allow_html=True,
            )
            st.write("")
            st.markdown(
                "<div class='decision-note'><b>Exact contracts:</b> "
                f"{recommendation.get('optimisation_explanation', 'N/A')}</div>",
                unsafe_allow_html=True,
            )
        with right:
            st.markdown("### Market context")
            market_table = pd.DataFrame(
                [
                    ("Current price", money(market.get("current_price"))),
                    (
                        "Trend",
                        str(market.get("trend_label", "N/A"))
                        .replace("_", " ")
                        .title(),
                    ),
                    (
                        "Outlook alignment",
                        str(market.get("outlook_alignment", "N/A")).title(),
                    ),
                    (
                        "IV regime",
                        str(market.get("volatility_regime", "N/A"))
                        .replace("_", " ")
                        .title(),
                    ),
                    ("Expected move", money(market.get("expected_move"))),
                    (
                        "Expected range",
                        f"{money(market.get('expected_lower_price'))} to "
                        f"{money(market.get('expected_upper_price'))}",
                    ),
                ],
                columns=["Item", "Value"],
            )
            st.dataframe(market_table, hide_index=True, use_container_width=True)
            st.markdown("### Risk and cost")
            st.write(
                "Entry: **"
                f"{str(recommendation.get('entry_type', 'N/A')).title()} "
                f"{money(recommendation.get('entry_amount_before_explicit_cost'))}"
                "** before explicit cost"
            )
            st.write(
                "Estimated transaction cost: **"
                f"{money(recommendation.get('estimated_transaction_cost'))}**"
            )
            st.write(
                "Expected return on max risk: **"
                f"{percent(recommendation.get('net_expected_return_on_risk'))}**"
            )
            st.write(
                "Liquidity score: **"
                f"{number(recommendation.get('liquidity_score'))}/100**"
            )
            st.write(
                "GA fitness: **"
                f"{number(recommendation.get('fitness_score'), digits=2)}/100**"
            )

    with payoff_tab:
        st.markdown("### Cost-adjusted expiration payoff")
        payoff_curve = run["payoff_curve"]
        assert isinstance(payoff_curve, pd.DataFrame)
        if {"terminal_stock_price", "profit_loss"}.issubset(payoff_curve.columns):
            payoff = payoff_curve.set_index("terminal_stock_price")[["profit_loss"]]
            st.line_chart(
                payoff,
                x_label="Terminal stock price",
                y_label="Profit / loss (USD)",
            )
        else:
            st.info("No valid payoff curve was produced for this recommendation.")

        st.markdown("### Expected-move scenarios")
        st.dataframe(
            run["payoff_scenarios"],
            hide_index=True,
            use_container_width=True,
            column_config={
                "terminal_stock_price": st.column_config.NumberColumn(
                    "Terminal price",
                    format="$%.2f",
                ),
                "profit_loss": st.column_config.NumberColumn(
                    "Profit / loss",
                    format="$%.2f",
                ),
            },
        )
        st.caption(
            "Expiration payoff only; the path before expiry can differ because "
            "of volatility, time decay and assignment risk."
        )

    with alternatives_tab:
        st.markdown("### Highest-ranked alternatives")
        alternatives = run["alternatives"]
        assert isinstance(alternatives, pd.DataFrame)
        alternative_columns = _available_columns(
            alternatives,
            [
                "fitness_rank",
                "strategy_name",
                "expiry",
                "long_strike",
                "short_strike",
                "adjusted_expected_profit",
                "probability_of_profit",
                "adjusted_max_loss",
                "liquidity_score",
                "fitness_score",
            ],
        )
        st.dataframe(
            alternatives[alternative_columns],
            hide_index=True,
            use_container_width=True,
        )

    with evidence_tab:
        st.markdown("### Pipeline readiness")
        pipeline_status = run["pipeline_status"]
        assert isinstance(pipeline_status, pd.DataFrame)
        st.dataframe(pipeline_status, hide_index=True, use_container_width=True)
        if {"stage", "pass_rate"}.issubset(pipeline_status.columns):
            readiness = pipeline_status.set_index("stage")[["pass_rate"]] * 100
            st.bar_chart(
                readiness,
                x_label="Pipeline stage",
                y_label="Checks passed (%)",
            )

        st.markdown("### Quantitative method comparison")
        method_comparison = run["method_comparison"]
        assert isinstance(method_comparison, pd.DataFrame)
        comparison_columns = _available_columns(
            method_comparison,
            [
                "method",
                "adjusted_expected_profit",
                "probability_of_profit",
                "net_expected_return_on_risk",
                "adjusted_max_loss",
                "liquidity_score",
                "fitness_score",
                "stress_expected_profit",
                "stress_probability_of_profit",
            ],
        )
        st.dataframe(
            method_comparison[comparison_columns],
            hide_index=True,
            use_container_width=True,
        )
        st.write(
            "Historical-return stress probability of profit: **"
            f"{percent(evaluation.get('historical_stress_probability_of_profit'))}**"
        )
        st.write(
            "Gap to exhaustive oracle: **"
            f"{number(evaluation.get('gap_to_exhaustive_oracle'), digits=4)} "
            "fitness points**"
        )

    with limitations_tab:
        st.markdown("### Known limitations")
        st.dataframe(run["limitations"], hide_index=True, use_container_width=True)
        st.markdown(
            "<div class='risk-note'><b>Important:</b> The system uses "
            "current-chain modelling and historical-underlying stress "
            "simulation. It does not claim a full historical-options "
            "backtest.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.warning(
        str(payload.get("disclaimer", "Decision support only; not trading advice."))
    )


st.title("Options Strategy Recommendation and Optimisation System")
st.caption(
    "Generate a fresh, explainable recommendation from the notebook pipeline "
    "for one ticker and directional outlook."
)

with st.sidebar:
    st.header("Analysis request")
    with st.form("analysis-request", border=False):
        ticker_input = st.text_input("Stock ticker", value="AAPL", max_chars=15)
        outlook_input = st.radio(
            "Directional outlook",
            options=["Bullish", "Bearish"],
            horizontal=True,
        )
        generate = st.form_submit_button(
            "Generate recommendation",
            type="primary",
            use_container_width=True,
        )
    st.markdown("---")
    st.caption(
        "Each request runs Notebooks 1–7 with fresh market data. "
        "Results are temporary and are not preloaded."
    )
    st.markdown("**Currently supported option strategies**")
    st.markdown(
        "- **Bullish:** Bull Call Spread, Bull Put Spread, Long Call\n"
        "- **Bearish:** Bear Put Spread, Bear Call Spread, Long Put"
    )
    st.caption(
        "Exact expiries and strikes depend on the live option chain, "
        "liquidity, and the pipeline's validation checks."
    )

if generate:
    status = None
    completed_run = None
    try:
        selected_ticker = normalise_ticker(ticker_input)
        selected_outlook = normalise_outlook(outlook_input)
        status = st.status("Preparing the notebook pipeline…", expanded=True)

        def report_stage(current: int, total: int, notebook_name: str) -> None:
            label = notebook_name.removesuffix(".ipynb").replace("_", " ")
            status.update(label=f"Running stage {current} of {total}…")
            status.write(f"Stage {current}/{total}: {label}")

        completed_run = run_pipeline(
            selected_ticker,
            selected_outlook,
            on_progress=report_stage,
        )
        generated_result = load_run(
            completed_run.run_root,
            completed_run.ticker,
            completed_run.outlook,
        )
        st.session_state["pipeline_result"] = generated_result
        status.update(label="Recommendation generated", state="complete", expanded=False)
    except (PipelineExecutionError, ValueError, FileNotFoundError) as error:
        if status is not None:
            status.update(label="Pipeline could not complete", state="error", expanded=True)
        st.error(str(error))
    finally:
        if completed_run is not None:
            discard_run(completed_run)

saved_result = st.session_state.get("pipeline_result")
if not saved_result:
    st.info(
        "Enter a ticker and outlook, then select **Generate recommendation**. "
        "The app will run the analytical pipeline for that request."
    )
    st.stop()

render_recommendation(saved_result)

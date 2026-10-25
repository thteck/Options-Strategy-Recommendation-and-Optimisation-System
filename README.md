# Options Strategy Recommendation and Optimisation System

## SECTION 1 : PROJECT TITLE

**Options Strategy Recommendation and Optimisation System**

NUS-ISS · Graduate Certificate in Intelligent Reasoning Systems · Practice Module

| Item | Details |
| --- | --- |
| Group name / number | Group 3 - Options Strategy Recommendation and Optimization System |
| Full name | Tey Hao Teck |
| Student ID | A0362588M |
| Project repository | [Options Strategy Recommendation and Optimisation System](https://github.com/thteck/Options-Strategy-Recommendation-and-Optimisation-System) |
| Submission date | 25 Oct 2026 |

---

## SECTION 2 : EXECUTIVE SUMMARY / PAPER ABSTRACT

Selecting an options strategy requires investors to consider market direction, volatility, expiry dates, strike prices, liquidity and potential losses. Even with a bullish or bearish outlook, several strategies may be suitable, each with different costs and payoff characteristics. Manually comparing these alternatives can be time-consuming and inconsistent, particularly when the reasoning behind a recommendation is not clearly explained.

This project develops an end-to-end Options Strategy Recommendation and Optimisation System. Users enter a stock ticker and select a bullish or bearish outlook through a Streamlit interface. The system retrieves market and options data, derives market features, applies knowledge-based reasoning and evaluates feasible option strategies. A genetic algorithm searches across strategy types, expiry dates and strike prices to identify candidates that balance expected return, probability of profit, downside risk, capital requirements, liquidity and alignment with the reasoning layer.

The system combines explicit financial rules, a knowledge graph, Monte Carlo payoff simulation and evolutionary optimisation. Recommendations include the selected option legs, supporting reasoning, risk and cost information, payoff visualisations and alternative strategies. Optimisation experiments compare the genetic algorithm with a baseline and exhaustive ranking, while a separate notebook evaluates simulated historical trades using SPY options data from 2020–2022.

The project demonstrates how intelligent reasoning techniques can support transparent financial decision-making. It is an educational decision-support prototype and does not execute trades. Simulation estimates and retrospective backtesting results do not establish future profitability.

### Project objectives

- Automate market-data collection and options-strategy comparison from a ticker and user-selected outlook.
- Represent domain knowledge through explicit rules and a knowledge graph.
- Optimise feasible strategy types, expiries and strikes using a genetic algorithm.
- Explain recommendations through option-leg details, financial metrics and visualisations.
- Evaluate optimisation quality, stability, cost sensitivity and historical simulated outcomes.

### Supported strategies

| Market outlook | Strategies |
| --- | --- |
| Bullish | Long call, bull call spread, bull put spread |
| Bearish | Long put, bear put spread, bear call spread |

### Intelligent reasoning techniques

| IRS technique group | Application in this project |
| --- | --- |
| Decision automation / knowledge-based reasoning | Rules connect market outlook, volatility and expected movement with suitable option strategies. |
| Business resource optimisation / evolutionary computing | A genetic algorithm searches feasible strategy types, expiry dates and strike combinations using a weighted fitness function. |
| Cognitive techniques / knowledge representation | A knowledge graph represents relationships between market conditions and strategies and supports explanation of the recommendations. |

These three groups form the project's primary technique mapping. Detailed implementation evidence and the MR, RS and CGS course mapping belong in the group report.

---

## SECTION 3 : CREDITS / PROJECT CONTRIBUTION

Complete and verify the following table before submission. Add one row for each additional member.

| Official Full Name | Student ID / Permitted Masked ID | Work Items (Who Did What) | Email (Optional) |
| --- | --- | --- | --- |
| Tey Hao Teck | A0362588M | **[End-to-end system development]** | teyhaoteck@u.nus.edu |

---

## SECTION 4 : VIDEO OF SYSTEM MODELLING & USE CASE DEMO

| Video | Coverage | Link |
| --- | --- | --- |
| Promotion and use-case demonstration — 5 minutes | Business problem, value proposition, user demonstration and proposed pricing model. | [Watch business video](https://youtu.be/qE9FIpF5Htc) |
| System design and technical explanation — 5 minutes | Architecture, data preparation, reasoning, payoff simulation, genetic algorithm and evaluation. | [Watch technical video](https://youtu.be/eqTqprOWrKI) |

Suggested demonstration: enter a ticker, select an outlook, generate a recommendation, inspect the option legs and explanation, and review payoff and evaluation evidence. Show the historical backtest separately from the live recommendation workflow.

The supplied module briefing does not permit AI-generated presentation speech.

---

## SECTION 5 : USER GUIDE

### 5.1 Requirements

- Python 3.11 or later; Python 3.12.10 was used during project development.
- Git for cloning the repository, or a downloaded repository ZIP.
- Internet access for installation and live market-data retrieval.
- A web browser for the Streamlit interface.

Core dependencies include Streamlit, pandas, NumPy, Matplotlib, yfinance, Papermill, IPython kernel support, NetworkX and RDFLib. Use `application/requirements.txt` for the application's dependency specifications.

### 5.2 Download and install

Run these commands in a terminal:

```bash
git clone https://github.com/thteck/Options-Strategy-Recommendation-and-Optimisation-System.git
cd Options-Strategy-Recommendation-and-Optimisation-System
python -m venv .venv
```

Activate the environment using the command for your terminal:

| Terminal | Command |
| --- | --- |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv/bin/activate` |

Install the application dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r application/requirements.txt
```

### 5.3 Start the application

From the repository root:

```bash
python -m streamlit run application/app.py
```

Open the local URL printed in the terminal, normally `http://localhost:8501`.

1. Enter a ticker with available options data, such as `AAPL`.
2. Select **Bullish** or **Bearish**.
3. Click **Generate recommendation**.
4. Wait for the seven analytical stages to complete; a run may take several minutes.
5. Review the recommended option legs, explanation, risk and costs, payoff curve, alternatives and evaluation evidence.

The outlook is supplied by the user; the live application does not independently choose the user's market direction.

### 5.4 Pipeline and repository structure

| File / directory | Purpose |
| --- | --- |
| `application/app.py` | Streamlit user interface and result display. |
| `application/pipeline.py` | Parameterises and executes Notebooks 01–07 for each request. |
| `application/requirements.txt` | Application dependencies. |
| `pipeline_notebooks/01_Data_Collection_and_Preparation.ipynb` | Collects and prepares market and options data. |
| `pipeline_notebooks/02_Market_Feature_Engineering.ipynb` | Derives market features used by the reasoning and evaluation stages. |
| `pipeline_notebooks/03_Knowledge_Graph_and_Rule_Reasoning.ipynb` | Applies knowledge-graph and rule-based strategy reasoning. |
| `pipeline_notebooks/04_Option_Strategy_Payoff_Engine.ipynb` | Constructs feasible strategies and evaluates payoff and simulated outcomes. |
| `pipeline_notebooks/05_Genetic_Algorithm_Strategy_Optimisation.ipynb` | Optimises strategies and benchmarks the genetic algorithm. |
| `pipeline_notebooks/06_Experiments_and_Evaluation.ipynb` | Evaluates the analytical pipeline. |
| `pipeline_notebooks/07_End_to_End_System_Demo.ipynb` | Produces the validated recommendation payload. |
| `pipeline_notebooks/08_Historical_Options_Backtesting.ipynb` | Runs a separate historical SPY options experiment. |
| `backtest_dataset/spy_2020_2022.csv` | Historical options dataset used by Notebook 08. |

The live application runs **Notebooks 01–07 only**. Each request uses an isolated temporary working directory and retrieves fresh data. Requests are serialised within one Streamlit process. Temporary run files are removed after the app loads the results, which remain scoped to the active session.

## SECTION 6 : PROJECT REPORT / PAPER

**Group report:** **[ProjectReport](https://github.com/thteck/Options-Strategy-Recommendation-and-Optimisation-System/blob/main/ProjectReport/TeyHaoTeck_Final%20Report.pdf)]**

### Report structure

1. Executive summary and project introduction.
2. Business problem, background and market research.
3. Objectives, scope and success measurements.
4. Data collection and preparation.
5. System architecture, domain knowledge and reasoning design.
6. Implementation of payoff simulation, optimisation and the user interface.
7. Experiments, quantitative evaluation and historical backtesting.
8. Findings, limitations and discussion.
9. Conclusions and future work.
10. Appendices: project proposal; MR, RS and CGS functionality mapping; installation and user guide; references; acknowledgements and AI-use disclosure where applicable.

Individual reflection and peer evaluation should be submitted separately and confidentially as specified in the supplied module briefing.

### Evaluation evidence

| Evaluation area | Evidence to include in the final report |
| --- | --- |
| Reasoning correctness | Representative scenarios, rule coverage and consistency between conditions, strategies and explanations. |
| Optimisation quality | GA fitness compared with the rule/payoff baseline and exhaustive oracle; optimality gap and convergence. |
| Repeatability | Variation across repeated random seeds. |
| Execution-cost sensitivity | Recommendation changes under 0×, 1× and 2× the configured cost estimate. |
| Historical simulation | Trade count, win rate, average win/loss, net P&L, strategy/year breakdown and skipped or unresolved outcomes. |
| End-to-end usability | Successful input-to-result demonstrations and handling of invalid or unavailable data. |

**Final numerical results:** **[Insert verified results from the completed experiments.]**

### Interpretation and limitations

- Monte Carlo probability of profit is a model estimate, not a historical win rate. In Notebook 05, the inherited probability estimate includes bid/ask entry pricing but excludes the additional explicit cost estimate used in the optimisation fitness.
- The historical selection policy was revised after examining the same dataset. Its chronological replay uses past information at each decision, but its results are retrospective and are not an untouched out-of-sample test.
- The historical experiment defaults to the dataset's underlying snapshot as an expiry-price proxy. A separately supplied official-price file can be configured in the notebook.
- Early exercise, assignment and physical share delivery are not simulated. Historical open interest is unavailable, so the adapter uses volume and spread quality for liquidity scoring.
- Backtest results are trade-level realised P&L, not complete portfolio returns or mark-to-market drawdown. Overlapping maximum-loss limits do not constitute a full margin or account model.
- Current market-data availability, quote quality and execution assumptions affect the reliability of recommendations.

### Future work

- Validate the selection policy on new, previously unused historical dates.
- Improve historical coverage, official expiry prices and execution modelling.
- Add portfolio-level capital allocation, position sizing and mark-to-market risk assessment.
- Extend the strategy universe and compare alternative optimisation methods.
- Improve data-provider resilience and deployment performance.

---

## SECTION 7 : MISCELLANEOUS

### Data and supporting materials

- **Live market data:** Yahoo Finance through `yfinance`.
- **Historical data source:** [SPY Daily EOD Options Quotes 2020–2022](https://www.kaggle.com/datasets/kylegraupe/spy-daily-eod-options-quotes-2020-2022).
- **Historical data location:** `backtest_dataset/spy_2020_2022.csv`.
- **Submission template:** [IRS-PM Workshop Project Submission Template](https://github.com/IRS-PM/Workshop-Project-Submission-Template/blob/master/README.md).
- **Module references:** the supplied IRS Practice Module v2.16 briefing and project proposal/final presentation guidelines v015.


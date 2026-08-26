# Options Strategy Recommendation Application

## What it does

This Streamlit app generates a fresh, single-ticker recommendation on demand.
When the user selects **Generate recommendation**, it runs the parameterised
analysis Notebooks 1–7 in order:

1. data collection and preparation;
2. market feature engineering;
3. knowledge-graph rule reasoning;
4. option strategy payoff engine;
5. genetic-algorithm strategy optimisation;
6. experiments and evaluation; and
7. the validated end-to-end recommendation payload.

Notebook 8 is intentionally not run when a user clicks the button. Its role is
to generate a static Streamlit application, so running it inside the deployed
application would overwrite the app rather than produce more analysis. This
application is its delivery layer.

## Runtime behaviour

- The notebooks are sourced from the root-level `pipeline_notebooks/` folder.
- Each request has its own temporary working directory, so it does not load
  old batch results or collide with another request.
- Fresh market and options data are fetched for every generated recommendation.
- Once the result is loaded into the active Streamlit session, its temporary
  notebook files are removed. Results are therefore session-scoped, not a
  durable history.
- The app serialises requests in one Streamlit process because notebook
  execution is CPU- and network-intensive.

## Local run

Use Python 3.11 or later. From the project root:

```bash
pip install -r application/requirements.txt
streamlit run application/app.py
```

Then enter a ticker, choose **Bullish** or **Bearish**, and select
**Generate recommendation**. A typical run can take several minutes because
it fetches live data and evaluates candidate strategies.

## Streamlit Community Cloud

1. Put the `application/` and `pipeline_notebooks/` folders in a GitHub
   repository. The `Archive/` folder is not required by the deployed app.
2. Create a Community Cloud app and set the entrypoint to
   `application/app.py`.
3. Keep the dependency file at `application/requirements.txt`; Community
   Cloud recognises a requirements file beside the chosen entrypoint.
4. Deploy. The app uses paths derived from its own source file, so it does not
   depend on the current working directory.

Community Cloud local files are not durable. If you later need saved
recommendations, job recovery, or a shared history, add an external database
or object store and move long-running jobs to a worker service.

## Important limitation

This is decision support only. It does not execute trades, provide trading
advice, or claim a full historical-options backtest. Live quote and option
chain availability can change, and some tickers may not yield an eligible
strategy for a requested outlook.

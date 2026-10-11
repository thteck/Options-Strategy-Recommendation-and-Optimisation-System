"""Run the parameterised options notebooks for one Streamlit request.

The parameterised source copies live in ``pipeline_notebooks`` at the project
root. Each request receives an isolated temporary working directory, so it
never relies on pre-generated CSV/JSON files and concurrent requests cannot
overwrite one another's data.
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import sys
import tempfile
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import papermill as pm
from ipykernel.kernelspec import install as install_kernel_spec
from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel


APP_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_ROOT = APP_ROOT / "pipeline_notebooks"
RUNS_ROOT = Path(tempfile.gettempdir()) / "options-recommendation-runs"
KERNEL_PREFIX = RUNS_ROOT / "kernel-prefix"
KERNEL_NAME = "options-recommendation"
CELL_TIMEOUT_SECONDS = 300

ProgressCallback = Callable[[int, int, str], None]
_PIPELINE_LOCK = threading.RLock()


class PipelineExecutionError(RuntimeError):
    """Raised when an individual notebook does not produce a valid handoff."""

    def __init__(self, notebook_name: str, cause: BaseException | str) -> None:
        detail = str(cause).strip() or type(cause).__name__
        super().__init__(f"{notebook_name} failed: {detail[-2_000:]}")
        self.notebook_name = notebook_name


@dataclass(frozen=True)
class PipelineRun:
    """Location and identity of one completed, ephemeral notebook run."""

    ticker: str
    outlook: str
    run_root: Path

    @property
    def outputs_root(self) -> Path:
        return self.run_root / "outputs"


@dataclass(frozen=True)
class _Stage:
    number: int
    notebook_name: str
    parameters: dict[str, object]
    success_marker: Path


def normalise_ticker(value: str) -> str:
    """Validate a Yahoo-compatible equity ticker entered in the app."""
    ticker = value.strip().upper().replace(".", "-")
    if not re.fullmatch(r"[A-Z0-9.^=-]{1,15}", ticker):
        raise ValueError("Enter a valid ticker containing up to 15 supported characters.")
    return ticker


def normalise_outlook(value: str) -> str:
    outlook = value.strip().lower()
    if outlook not in {"bullish", "bearish"}:
        raise ValueError("Outlook must be bullish or bearish.")
    return outlook


def _ensure_kernel() -> str:
    """Install a kernel tied to the app's interpreter when one is unavailable.

    The pipeline notebooks were saved with a local-only ``tf-gpu`` kernel.
    Papermill is explicitly pointed at this portable kernel instead.
    """
    # A Streamlit process may not have permission to write to (or discover)
    # the user's global Jupyter data directory. Keep the portable spec beside
    # the other temporary runtime files and make it discoverable to Papermill.
    kernel_data_dir = KERNEL_PREFIX / "share" / "jupyter"
    existing_paths = os.environ.get("JUPYTER_PATH", "")
    path_entries = [entry for entry in existing_paths.split(os.pathsep) if entry]
    if str(kernel_data_dir) not in path_entries:
        os.environ["JUPYTER_PATH"] = os.pathsep.join(
            [str(kernel_data_dir), *path_entries]
        )

    manager = KernelSpecManager()
    try:
        spec = manager.get_kernel_spec(KERNEL_NAME)
        existing_executable = Path(spec.argv[0]).resolve()
        install_needed = existing_executable != Path(sys.executable).resolve()
    except (NoSuchKernel, IndexError, OSError):
        install_needed = True

    if install_needed:
        install_kernel_spec(
            kernel_spec_manager=manager,
            prefix=str(KERNEL_PREFIX),
            kernel_name=KERNEL_NAME,
            display_name="Python (Options Recommendation)",
            # Keep notebook execution independent from packages a local user
            # site may happen to contain. Community Cloud has an isolated
            # environment already; this also makes local Anaconda runs stable.
            env={"MPLBACKEND": "Agg", "PYTHONNOUSERSITE": "1"},
        )
    return KERNEL_NAME


def _discard_run_root(run_root: Path) -> None:
    """Remove a known temporary run without touching project files."""
    expected_parent = RUNS_ROOT.resolve()
    resolved_run = run_root.resolve()
    if resolved_run.parent != expected_parent:
        raise ValueError("Refusing to remove a run outside the temporary pipeline directory.")
    shutil.rmtree(resolved_run, ignore_errors=True)


def discard_run(run: PipelineRun) -> None:
    """Remove a temporary run after its output has been loaded into memory."""
    _discard_run_root(run.run_root)


def _missing_marker_detail(stage: _Stage) -> str:
    """Return Notebook 1's per-ticker diagnostic when it is available."""
    if stage.number != 1:
        return "The notebook finished without its required success marker."

    report_path = stage.success_marker.parent.parent / "batch_report.csv"
    try:
        with report_path.open("r", encoding="utf-8", newline="") as report:
            ticker = str(stage.parameters["TICKERS"][0])
            for row in csv.DictReader(report):
                if row.get("ticker") == ticker and row.get("error"):
                    return f"Data collection did not complete for {ticker}: {row['error']}"
    except (KeyError, OSError):
        pass

    return "The notebook finished without its required success marker."


def _stage_plan(ticker: str, outlook: str, run_root: Path) -> list[_Stage]:
    outputs_root = run_root / "outputs"
    ticker_root = outputs_root / "notebook_01" / ticker

    stages = [
        _Stage(
            1,
            "01_Data_Collection_and_Preparation.ipynb",
            {
                "RUN_MODE": "single",
                "TICKERS": [ticker],
                "MAX_TICKERS": 1,
                "SKIP_COMPLETED_TICKERS": False,
                "REQUEST_PAUSE_SECONDS": 0.0,
                "DISPLAY_SAMPLE": False,
            },
            ticker_root / "_SUCCESS.json",
        ),
        _Stage(
            2,
            "02_Market_Feature_Engineering.ipynb",
            {"TICKER": ticker},
            outputs_root / "notebook_02" / ticker / "_SUCCESS.json",
        ),
    ]

    for number, notebook_name in (
        (3, "03_Knowledge_Graph_and_Rule_Reasoning.ipynb"),
        (4, "04_Option_Strategy_Payoff_Engine.ipynb"),
        (5, "05_Genetic_Algorithm_Strategy_Optimisation.ipynb"),
        (6, "06_Experiments_and_Evaluation.ipynb"),
        (7, "07_End_to_End_System_Demo.ipynb"),
    ):
        stages.append(
            _Stage(
                number,
                notebook_name,
                {"TICKER": ticker, "OUTLOOK": outlook},
                outputs_root / f"notebook_{number:02d}" / ticker / outlook / "_SUCCESS.json",
            )
        )

    return stages


def run_pipeline(
    ticker: str,
    outlook: str,
    on_progress: ProgressCallback | None = None,
) -> PipelineRun:
    """Execute Notebooks 1–7 for one ticker/outlook and return its run folder.

    Notebook 8 is intentionally not run here: it packages a Streamlit app and
    would overwrite the deployed app.  This app is the Notebook 8 delivery
    layer and directly renders Notebook 7's validated payload instead.
    """
    ticker = normalise_ticker(ticker)
    outlook = normalise_outlook(outlook)
    missing_sources = [
        name
        for name in (
            "01_Data_Collection_and_Preparation.ipynb",
            "02_Market_Feature_Engineering.ipynb",
            "03_Knowledge_Graph_and_Rule_Reasoning.ipynb",
            "04_Option_Strategy_Payoff_Engine.ipynb",
            "05_Genetic_Algorithm_Strategy_Optimisation.ipynb",
            "06_Experiments_and_Evaluation.ipynb",
            "07_End_to_End_System_Demo.ipynb",
        )
        if not (NOTEBOOK_ROOT / name).exists()
    ]
    if missing_sources:
        raise FileNotFoundError(
            "Pipeline notebook source is missing: " + ", ".join(missing_sources)
        )

    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    run_root = Path(
        tempfile.mkdtemp(prefix=f"{ticker.lower()}-{outlook}-", dir=RUNS_ROOT)
    )
    stages = _stage_plan(ticker, outlook, run_root)

    try:
        # Papermill execution and kernel installation touch process-wide Jupyter
        # state. Serialising requests prevents two users from clobbering it.
        with _PIPELINE_LOCK:
            kernel_name = _ensure_kernel()
            total = len(stages)
            for index, stage in enumerate(stages, start=1):
                if on_progress is not None:
                    on_progress(index, total, stage.notebook_name)

                executed_path = run_root / "executed_notebooks" / stage.notebook_name
                executed_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    pm.execute_notebook(
                        input_path=NOTEBOOK_ROOT / stage.notebook_name,
                        output_path=executed_path,
                        parameters=stage.parameters,
                        kernel_name=kernel_name,
                        cwd=run_root,
                        progress_bar=False,
                        log_output=False,
                        start_timeout=120,
                        execution_timeout=CELL_TIMEOUT_SECONDS,
                    )
                except Exception as error:
                    raise PipelineExecutionError(stage.notebook_name, error) from error

                if not stage.success_marker.exists():
                    raise PipelineExecutionError(
                        stage.notebook_name,
                        _missing_marker_detail(stage),
                    )
    except BaseException:
        _discard_run_root(run_root)
        raise

    return PipelineRun(ticker=ticker, outlook=outlook, run_root=run_root)

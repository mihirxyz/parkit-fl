"""
Federated Learning metrics router.

Routes (under /api/v1/fl):
    GET /metrics – return FL experiment results from fl_metrics.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/fl", tags=["federated_learning"])

_FL_METRICS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "ml" / "results" / "fl_metrics.json"
)
_CENTRALIZED_METRICS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ml"
    / "results"
    / "centralized_metrics.json"
)


class FLMetricsResponse(BaseModel):
    experiment: dict[str, Any]
    global_model_history: list[dict[str, Any]]
    final_round: dict[str, Any] | None = None
    centralized_baseline: dict[str, Any] | None = None


@router.get("/metrics", response_model=FLMetricsResponse, status_code=status.HTTP_200_OK)
def get_fl_metrics() -> FLMetricsResponse:
    """Return latest Federated Learning evaluation metrics and round history."""
    if not _FL_METRICS_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FL metrics not found. Run the FL experiment first.",
        )

    with open(_FL_METRICS_PATH, "r", encoding="utf-8") as f:
        fl_data = json.load(f)

    cent_data: dict[str, Any] | None = None
    if _CENTRALIZED_METRICS_PATH.exists():
        with open(_CENTRALIZED_METRICS_PATH, "r", encoding="utf-8") as f:
            cent_data = json.load(f)

    history = fl_data.get("global_model_history", [])
    final_round = history[-1] if history else None

    return FLMetricsResponse(
        experiment=fl_data.get("experiment", {}),
        global_model_history=history,
        final_round=final_round,
        centralized_baseline=cent_data,
    )

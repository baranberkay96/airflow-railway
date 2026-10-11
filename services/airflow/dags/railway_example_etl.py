"""Example ETL pipeline (TaskFlow API) shipped with the Railway template.

Runs extract -> transform -> load on the Celery workers. Replace this folder
with your own DAG repository (see AIRFLOW_DAGS_GIT_URL).
"""

from __future__ import annotations

import logging
from datetime import datetime

from airflow.sdk import dag, task

log = logging.getLogger(__name__)


@dag(
    dag_id="railway_example_etl",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["example", "railway"],
)
def railway_example_etl() -> None:
    @task
    def extract() -> list[dict]:
        return [
            {"order_id": 1, "amount": 120.0, "currency": "EUR"},
            {"order_id": 2, "amount": 75.5, "currency": "EUR"},
            {"order_id": 3, "amount": 310.25, "currency": "EUR"},
        ]

    @task
    def transform(orders: list[dict]) -> dict:
        total = round(sum(o["amount"] for o in orders), 2)
        return {"orders": len(orders), "revenue": total, "currency": "EUR"}

    @task
    def load(summary: dict) -> None:
        log.info("Daily summary: %s", summary)

    load(transform(extract()))


railway_example_etl()

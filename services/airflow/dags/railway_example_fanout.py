"""Example of dynamic task mapping: one task per item, spread over Celery workers.

Useful to check that scaling the airflow-worker service increases throughput.
"""

from __future__ import annotations

import time
from datetime import datetime

from airflow.sdk import dag, task


@dag(
    dag_id="railway_example_fanout",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["example", "railway"],
    params={"items": 12, "seconds_per_item": 5},
)
def railway_example_fanout() -> None:
    @task
    def make_batches(params: dict | None = None) -> list[int]:
        count = int((params or {}).get("items", 12))
        return list(range(count))

    @task
    def process(item: int, params: dict | None = None) -> int:
        time.sleep(int((params or {}).get("seconds_per_item", 5)))
        return item * item

    @task
    def summarise(results: list[int]) -> int:
        return sum(results)

    summarise(process.expand(item=make_batches()))


railway_example_fanout()

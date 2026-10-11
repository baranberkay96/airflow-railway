"""Print an Airflow 3 DAG bundle list (JSON) for a git repository.

Reads:
  AIRFLOW_DAGS_GIT_URL       https URL of the repository (required)
  AIRFLOW_DAGS_GIT_REF       branch, tag or commit to track (default: main)
  AIRFLOW_DAGS_GIT_SUBDIR    folder inside the repo that holds the DAGs (optional)
  AIRFLOW_DAGS_REFRESH_SECS  how often to fetch new commits (default: 120)
  AIRFLOW_DAGS_BUNDLE_NAME   bundle name shown in the UI (default: dags)

Credentials for private repositories come from the Airflow connection
``git_dags`` (env var AIRFLOW_CONN_GIT_DAGS). Public repositories need none.
"""

from __future__ import annotations

import json
import os
import sys


def build() -> list[dict]:
    url = os.environ.get("AIRFLOW_DAGS_GIT_URL", "").strip()
    if not url:
        raise SystemExit("AIRFLOW_DAGS_GIT_URL is empty")

    subdir = os.environ.get("AIRFLOW_DAGS_GIT_SUBDIR", "").strip().strip("/")
    kwargs: dict = {
        "repo_url": url,
        "tracking_ref": os.environ.get("AIRFLOW_DAGS_GIT_REF", "").strip() or "main",
        "git_conn_id": "git_dags",
        "refresh_interval": int(os.environ.get("AIRFLOW_DAGS_REFRESH_SECS", "") or 120),
    }
    if subdir:
        kwargs["subdir"] = subdir
        # Only check out the DAG folder (keeps monorepo checkouts small).
        kwargs["sparse_dirs"] = [subdir]

    return [
        {
            "name": os.environ.get("AIRFLOW_DAGS_BUNDLE_NAME", "").strip() or "dags",
            "classpath": "airflow.providers.git.bundles.git.GitDagBundle",
            "kwargs": kwargs,
        }
    ]


if __name__ == "__main__":
    json.dump(build(), sys.stdout)

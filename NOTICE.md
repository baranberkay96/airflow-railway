# NOTICE — Apache Airflow template

This is a community template. It is not affiliated with or endorsed by the Apache Software Foundation. Apache Airflow, Airflow and the Airflow logo are trademarks of the Apache Software Foundation.

## Upstream sources checked (2026-10-10)

| Source | Version / path | License | Use |
|---|---|---|---|
| apache/airflow | `3.3.2`: https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml | Apache-2.0 | Reference topology (api-server, scheduler, dag-processor, triggerer, celery worker, init, Postgres, Redis) and environment variables |
| apache/airflow | `3.3.2`: `Dockerfile` (embedded `/entrypoint`), `airflow-core/src/airflow/cli/commands/api_server_command.py`, `airflow-core/src/airflow/utils/serve_logs/core.py`, `cli/cli_config.py` | Apache-2.0 | Entrypoint behaviour, api-server host/workers, log-server dual-stack bind |
| apache/airflow | `constraints-3.3.2/constraints-3.12.txt` | Apache-2.0 | Provider versions in the image |
| apache/airflow | `providers-git/0.5.0`: `providers/git/src/airflow/providers/git/bundles/git.py`, `hooks/git.py` | Apache-2.0 | GitDagBundle kwargs (`repo_url`, `tracking_ref`, `subdir`, `sparse_dirs`), git connection fields |
| encode/uvicorn | `0.52.4`: `uvicorn/config.py`, `uvicorn/main.py` | BSD-3-Clause | Confirms multi-worker mode binds an AF_INET6 socket without IPV6_V6ONLY |
| Amazon provider docs | AWS connection page | Apache-2.0 | `endpoint_url`, `region_name`, `config_kwargs` extras |
| Railway docs | Storage Buckets, start command, healthchecks | — | Bucket variables, virtual-hosted URLs, start command overrides ENTRYPOINT |

## Market templates and repos reviewed

| Code / repo | License | Use |
|---|---|---|
| `airflow` → github.com/gridalpha/airflow-railway | none (all rights reserved) | Read for ideas (service split, bucket logs, private-domain hostname for log serving, git bundle option). No files, code or text copied; all implementation written independently. |
| `kestra-workflow-engine`, `windmill-dev` → nomideusz/windmill-railway | n/a | Market positioning only |

## Railway base services

`Postgres` and `Redis` definitions are copied from `templates/_railway-base/postgres.json` and `redis.json` (Railway's own templates).

## Images used at runtime

- `apache/airflow:3.3.2` (Apache-2.0) — extended in `services/airflow/Dockerfile` with a launcher script, two helper modules and example DAGs, all written for this template.
- `ghcr.io/railwayapp-templates/postgres-ssl:18`, `redis:8.2`.

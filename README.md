# Deploy and Host Apache Airflow with Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/apache-airflow-3-data-pipelines)

Apache Airflow is the open-source platform for authoring, scheduling and monitoring data pipelines as Python code. This community template deploys Airflow 3 the way the project recommends for production — separate API server, scheduler, DAG processor, triggerer and Celery workers — on Railway with Postgres, Redis and bucket-backed task logs.

## About Hosting Apache Airflow

Airflow 3 is a set of cooperating processes. The API server serves the UI, the REST API and the Task Execution API; the scheduler decides what runs; the DAG processor parses your DAG files; the triggerer runs deferrable operators; Celery workers execute tasks, fed through Redis. All of them share a Postgres metadata database. On Railway, volumes cannot be shared between services, so this template delivers DAGs through Airflow 3 DAG bundles from a git repository (push to deploy, each run pinned to a commit) and stores task logs in a Railway Bucket. A one-shot init service migrates the database and creates the admin account before the other roles start.

## Common Use Cases

- Nightly and hourly ETL/ELT jobs that load data into Postgres, BigQuery, Snowflake or ClickHouse.
- Orchestrating dbt, Spark or Python batch jobs with retries, SLAs and alerting.
- Machine-learning pipelines: feature extraction, training and batch scoring.
- Event-driven workflows using deferrable operators and sensors.
- Replacing cron jobs spread across servers with one observable scheduler.

## Dependencies for Apache Airflow Hosting

- Apache Airflow 3 (`apache/airflow` image) with the Celery executor and FAB auth manager
- PostgreSQL (metadata database and Celery result backend)
- Redis (Celery broker)
- A git repository with your DAGs (an example repository path is preset)
- S3-compatible object storage for task logs (Railway Bucket)

### Deployment Dependencies

- Airflow documentation: https://airflow.apache.org/docs/apache-airflow/stable/
- Running Airflow in Docker (reference compose): https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html
- DAG bundles: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html
- Git provider (GitDagBundle): https://airflow.apache.org/docs/apache-airflow-providers-git/stable/index.html
- Amazon provider (S3 remote logging): https://airflow.apache.org/docs/apache-airflow-providers-amazon/stable/logging/s3-task-handler.html
- Docker image reference: https://airflow.apache.org/docs/docker-stack/index.html

### Implementation Details

| Service | Role | Public |
|---|---|---|
| `airflow-apiserver` | UI, REST API, Task Execution API | HTTPS domain |
| `airflow-scheduler` | Schedules DAG runs and queues tasks | — |
| `airflow-dag-processor` | Clones the DAG repo and parses DAGs | — |
| `airflow-triggerer` | Runs deferred tasks | — |
| `airflow-worker` | Celery worker (scale with replicas) | — |
| `airflow-init` | One-shot: `airflow db migrate` + admin user, then exits | — |
| `Postgres`, `Redis`, `Bucket` | Metadata DB, broker, task logs | — |

All Airflow services build the same thin image (`FROM apache/airflow:3.3.2`) and differ only by start command.

**First login.** Wait until `airflow-init` has finished and `airflow-apiserver` is healthy, then open its domain and sign in with `AIRFLOW_ADMIN_USERNAME` (default `admin`) and the generated `AIRFLOW_ADMIN_PASSWORD` from the `airflow-apiserver` Variables tab. The two example DAGs are paused; unpause and trigger them to test the workers.

**Use your own DAGs.** On `airflow-apiserver`, set `AIRFLOW_DAGS_GIT_URL` to your repository, `AIRFLOW_DAGS_GIT_REF` to the branch and `AIRFLOW_DAGS_GIT_SUBDIR` to the DAG folder (empty for the repo root); the other services reference these values. For a private repository add `AIRFLOW_CONN_GIT_DAGS` with an access token to every Airflow service. New commits are picked up automatically.

**Scaling.** Increase `airflow-worker` replicas for more parallel tasks, or `AIRFLOW__CELERY__WORKER_CONCURRENCY` for more slots per worker. Add triggerer replicas for many deferrable tasks.

**Pinning and upgrades.** The Airflow version is set by one `FROM` line in `services/airflow/Dockerfile`. Change it, push, and Railway rebuilds every Airflow service; `airflow-init` migrates the database and the other roles wait for the new schema.

### Why Deploy Apache Airflow on Railway?

Railway runs the full Airflow 3 stack — API server, scheduler, DAG processor, triggerer, workers, Postgres, Redis and log storage — in one project on a private network. You scale workers with a slider, ship DAGs with a git push, and pay for the resources your pipelines use.

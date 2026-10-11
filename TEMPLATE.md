# Apache Airflow 3 Data Pipelines — composer spec

| Field | Value |
|---|---|
| Listing name | **Apache Airflow 3 Data Pipelines** (version label `3` = Airflow major; already part of the LISTINGS.md name, so unchanged) |
| Description | Schedule and monitor DAGs with Celery workers, Redis and Postgres. Ready to scale. (82 chars, unchanged) |
| Category | Automation |
| Tags | airflow, data-pipelines, etl, orchestration, celery, python |
| Base market template | `airflow` (gridalpha/airflow-railway: Airflow 3 split into api-server / scheduler / dag-processor / triggerer / worker + Redis + Postgres + Bucket logs). Its repo has **no license** → used for ideas only; every file here is newly written. `kestra-workflow-engine` and `windmill-dev` (the current "Airflow alternative" leaders) reviewed for positioning only. |
| Upstream checked | Apache Airflow `3.3.2` (2026-09-17): official `docker-compose.yaml` (https://airflow.apache.org/docs/apache-airflow/3.3.2/docker-compose.yaml), image `Dockerfile` entrypoint, `constraints-3.3.2/constraints-3.12.txt` (providers: git 0.5.0, amazon 9.36.0, fab 3.9.0, celery 3.24.0), `GitDagBundle` source (providers-git 0.5.0), uvicorn 0.52.4 socket binding. Pinned 2026-10-10. |

## Architecture

```
                 HTTPS
 users ───────────────────► airflow-apiserver :8080  (UI, REST API, Task Execution API)
                                 ▲   ▲
       execution API (private)   │   │ live logs :8793 (private)
 airflow-worker ×N ──────────────┘   └────────────── airflow-worker
 airflow-triggerer ─────────────►┘
 airflow-scheduler ──► Redis (Celery broker) ──► airflow-worker ×N
 airflow-dag-processor ──► git repo (GitDagBundle) ──► serialized DAGs in Postgres
 all roles ──► Postgres (metadata + Celery results)
 worker / triggerer / dag-processor ──► Railway Bucket (task logs) ◄── airflow-apiserver (reads logs)
 airflow-init (one-shot): airflow db migrate + create admin user, then exits
```

## Services

All six Airflow services build the **same** image from `services/airflow` (`FROM apache/airflow:3.3.2`) and differ only by start command.

| Service | Source | Start command | Public | Healthcheck | Volume | Restart | Replicas |
|---|---|---|---|---|---|---|---|
| `airflow-init` | repo `/services/airflow` | `/opt/railway/bin/railway-airflow init` | — | — (one-shot, exits 0) | — | ON_FAILURE ×5 | 1 |
| `airflow-apiserver` | same | `/opt/railway/bin/railway-airflow api-server` | domain → 8080 | `/api/v2/monitor/health`, 900 s | — | ON_FAILURE ×10 | 1 |
| `airflow-scheduler` | same | `… scheduler` | — | `/health` on PORT=8974, 900 s | — | ON_FAILURE ×10 | 1 |
| `airflow-dag-processor` | same | `… dag-processor` | — | — (no HTTP) | — | ON_FAILURE ×10 | 1 |
| `airflow-triggerer` | same | `… triggerer` | — | — (no HTTP) | — | ON_FAILURE ×10 | 1 |
| `airflow-worker` | same | `… worker` | — | — (no HTTP) | — | ON_FAILURE ×10 | 1 (scale up) |
| `Postgres` | `ghcr.io/railwayapp-templates/postgres-ssl:18` (copied from `_railway-base/postgres.json`) | image | — | — | `/var/lib/postgresql/data` | ON_FAILURE | 1 |
| `Redis` | `redis:8.2` (copied from `_railway-base/redis.json`) | base start command | — | — | `/data` | ON_FAILURE | 1 |
| `Bucket` | Railway Bucket | — | — | — | — | — | — |

The 900 s healthcheck timeouts cover the first boot, where every role waits (`airflow db check-migrations`) until `airflow-init` has migrated the database.

## Variables

**Owned by `airflow-apiserver`** (other Airflow services reference them as `${{airflow-apiserver.<NAME>}}`):

| Variable | Default | Notes |
|---|---|---|
| `AIRFLOW__CORE__FERNET_KEY` | `${{secret(43, base64url)}}=` | 32-byte url-safe base64 key. Must be identical everywhere and never change (it encrypts stored connections). |
| `AIRFLOW__API_AUTH__JWT_SECRET` | `${{secret(48)}}` | Signs task-execution tokens. |
| `AIRFLOW__API__SECRET_KEY` | `${{secret(48)}}` | API / log-server secret. |
| `AIRFLOW_CONN_RAILWAY_BUCKET` | JSON AWS connection built from `${{Bucket.ACCESS_KEY_ID}}`, `SECRET_ACCESS_KEY`, `ENDPOINT`, `REGION`, virtual-hosted addressing | Used for remote task logs. |
| `AIRFLOW_DAGS_GIT_URL` | `https://github.com/baranberkay96/airflow-railway.git` | Repo for the GitDagBundle. Set to your own repo. Empty → example DAGs baked into the image. |
| `AIRFLOW_DAGS_GIT_REF` | `main` | Branch/tag/commit. |
| `AIRFLOW_DAGS_GIT_SUBDIR` | `services/airflow/dags` | Folder in the repo with DAG files; also used as sparse checkout. |
| `AIRFLOW_DAGS_REFRESH_SECS` | `120` | Fetch interval for new commits. |
| `AIRFLOW_ADMIN_USERNAME` / `AIRFLOW_ADMIN_PASSWORD` / `AIRFLOW_ADMIN_EMAIL` | `admin` / `${{secret(24)}}` / `admin@example.com` | Created once by `airflow-init` (FAB auth manager). |
| `PORT`, `AIRFLOW__API__PORT` | `8080` | |
| `AIRFLOW__API__HOST` | `::` | With `AIRFLOW__API__WORKERS=2`, uvicorn binds a dual-stack socket (IPv4 + IPv6 private network). |
| `AIRFLOW__API__WORKERS` | `2` | |
| `AIRFLOW__API__BASE_URL` | `https://${{RAILWAY_PUBLIC_DOMAIN}}` | |
| `FORWARDED_ALLOW_IPS` | `*` | Lets uvicorn honour Railway's `X-Forwarded-Proto`. |

**On every Airflow service** (including `airflow-apiserver`):

| Variable | Default |
|---|---|
| `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | `${{Postgres.DATABASE_URL}}` (Celery result backend `db+…` derived by the launcher) |
| `AIRFLOW__CELERY__BROKER_URL` | `${{Redis.REDIS_URL}}/0` |
| `AIRFLOW__CORE__EXECUTION_API_SERVER_URL` | `http://${{airflow-apiserver.RAILWAY_PRIVATE_DOMAIN}}:8080/execution/` |
| `AIRFLOW__LOGGING__REMOTE_LOGGING` | `True` |
| `AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER` | `s3://${{Bucket.BUCKET}}/task-logs` |
| `AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID` | `railway_bucket` |

**Role-specific:** `airflow-scheduler`: `PORT=8974`, `AIRFLOW__SCHEDULER__SCHEDULER_HEALTH_CHECK_SERVER_PORT=8974`. `airflow-worker`: `AIRFLOW__CELERY__WORKER_CONCURRENCY=8`, `RAILWAY_DEPLOYMENT_DRAINING_SECONDS=300`. `airflow-init`: admin variables referenced from the api-server.

**Baked into the image** (`ENV` in the Dockerfile, override per service if needed): `AIRFLOW__CORE__EXECUTOR=CeleryExecutor`, `AIRFLOW__CORE__AUTH_MANAGER=…FabAuthManager`, `AIRFLOW__CORE__LOAD_EXAMPLES=False`, `AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True`, `AIRFLOW__CORE__HOSTNAME_CALLABLE=railway_airflow.hostname.private_domain`, `AIRFLOW__LOGGING__DELETE_LOCAL_LOGS=True`, `AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=True`.

**Optional:** `AIRFLOW_CONN_GIT_DAGS` on all Airflow services for a private DAG repo, e.g. `{"conn_type": "git", "host": "https://github.com/acme/dags.git", "login": "x-access-token", "password": "<token>"}`.

## DAG delivery (no shared volume)

Railway volumes attach to one service only, so the upstream compose layout (one `dags/` folder mounted into every container) is not possible. This template uses **Airflow 3 DAG bundles**:

1. `railway-airflow` builds `AIRFLOW__DAG_PROCESSOR__DAG_BUNDLE_CONFIG_LIST` from `AIRFLOW_DAGS_GIT_*` (a `GitDagBundle` with `repo_url`, `tracking_ref`, `subdir`, `sparse_dirs`, `refresh_interval`).
2. The dag-processor clones the repo, parses DAGs and stores them (with the commit) in Postgres; workers and the triggerer check out the exact commit a run was created with.
3. Push to the tracked branch → new DAG version within `AIRFLOW_DAGS_REFRESH_SECS`. No rebuild or redeploy.
4. Default: the template's own example DAGs (`services/airflow/dags`) in the template repository. If `AIRFLOW_DAGS_GIT_URL` is emptied, the same examples are served from the image (`dags-folder` bundle) so the stack still boots.
5. Setting `AIRFLOW__DAG_PROCESSOR__DAG_BUNDLE_CONFIG_LIST` directly (same value on all Airflow services) overrides all of this, e.g. for several bundles.

## Composer steps (Railway dashboard)

1. Add `Postgres` and `Redis` from the definitions in `_railway-base/` (names must stay `Postgres` / `Redis`). Add a Bucket named `Bucket`.
2. Create `airflow-apiserver` from GitHub repo `baranberkay96/airflow-railway`, root directory `/services/airflow`, start command `/opt/railway/bin/railway-airflow api-server`; paste its variables; generate a domain on port 8080; healthcheck `/api/v2/monitor/health`, timeout 900.
3. Duplicate it into `airflow-init`, `airflow-scheduler`, `airflow-dag-processor`, `airflow-triggerer`, `airflow-worker`; change the start command role; replace owned values with `${{airflow-apiserver.*}}` references; remove the domain; set healthcheck `/health` (scheduler only); set `airflow-init` restart policy to ON_FAILURE with 5 retries.
4. Deploy. Start-up order is handled in the launcher (no Railway ordering needed).

## Improvements over market templates

| Area | Market (`airflow`, gridalpha) | This template |
|---|---|---|
| Licensing | Source repo unlicensed (cannot be redistributed) | All files written for this template; NOTICE lists sources |
| Version | `apache/airflow:3.3.1` | `apache/airflow:3.3.2` (latest stable 3.x) |
| Migrations | Run inside api-server start-up | Dedicated one-shot `airflow-init` service (as in the official compose), with retries and an idempotent admin bootstrap |
| Shared secrets | Derived at runtime from one seed by a custom script | Plain Railway `${{secret()}}` values owned by the api-server and referenced by the others — visible and rotatable in the dashboard |
| IPv6 | `socat` relay processes added to the image | Native dual-stack binds: uvicorn `AIRFLOW__API__HOST=::` with 2 workers; Airflow's log servers bind `[::]` themselves; no extra processes or apt packages |
| DAGs | Baked into the image, git bundle optional | Git bundle by default (push-to-deploy DAGs, versioned runs), sparse checkout, image examples as fallback |
| Image | Extra apt packages, custom health server process | Thin layer: launcher script + 2 small Python helpers |
| Worker sizing | Concurrency 4 | Concurrency 8 per replica + 300 s draining for warm shutdown; scale with replicas |
| Docs | — | Private DAG repo connection, scaling, cost profile, verification list |

## Resource profile and cost (Railway: RAM $10/GB-mo, vCPU $20/mo, volume $0.15/GB-mo, bucket $0.015/GB-mo)

| Service | Idle RAM | Typical RAM | Idle CPU | Typical CPU |
|---|---|---|---|---|
| airflow-apiserver (2 uvicorn workers) | 0.7 GB | 0.9 GB | 0.02 | 0.1 |
| airflow-scheduler | 0.35 GB | 0.5 GB | 0.05 | 0.15 |
| airflow-dag-processor | 0.35 GB | 0.5 GB | 0.05 | 0.2 |
| airflow-triggerer | 0.25 GB | 0.35 GB | 0.01 | 0.05 |
| airflow-worker (×1, concurrency 8) | 0.45 GB | 1–2 GB | 0.02 | 0.5–1.0 |
| airflow-init | 0 (exits) | 0 | 0 | 0 |
| Postgres | 0.1 GB | 0.2 GB | 0.01 | 0.05 |
| Redis | 0.01 GB | 0.02 GB | 0 | 0.01 |
| **Total** | **~2.2 GB** | **~3.5–4.5 GB** | **~0.16 vCPU** | **~1.1–1.6 vCPU** |

Estimated monthly cost: **idle ≈ $26** (2.2 GB × $10 + 0.16 × $20 + ~1 GB volumes + bucket); **typical small data team ≈ $60–75**; each additional busy worker replica ≈ +$15–30.
Minimum plan: **Hobby** (eight services, ~2 GB baseline). Trial is not sufficient. **Pro** for several worker replicas or memory-heavy tasks.

## Scaling

- More parallel tasks: raise `airflow-worker` replicas (stateless; no volume) and/or `AIRFLOW__CELERY__WORKER_CONCURRENCY`.
- Many deferrable operators: add `airflow-triggerer` replicas.
- Large DAG repos: raise dag-processor memory or `AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES`.
- Scheduler HA: Airflow supports several schedulers on Postgres; add replicas to `airflow-scheduler` if needed.

## Pinning and upgrades

Pinned 2026-10-10: `apache/airflow:3.3.2` (one `FROM` line for all six Airflow services), `ghcr.io/railwayapp-templates/postgres-ssl:18`, `redis:8.2`. To upgrade: read the Airflow release notes, change the `FROM` tag, push → Railway rebuilds all Airflow services; `airflow-init` runs `airflow db migrate`, the others wait for the new schema before starting.

## Verification checklist

- [ ] `airflow-init` logs show `airflow db migrate` success, "admin user 'admin' created", exit code 0.
- [ ] `airflow-apiserver` healthy at `/api/v2/monitor/health`; log in at the public domain with `AIRFLOW_ADMIN_USERNAME` / `AIRFLOW_ADMIN_PASSWORD`.
- [ ] Health page shows scheduler, dag-processor and triggerer heartbeats as healthy.
- [ ] `railway_example_etl` and `railway_example_fanout` appear (bundle `dags`, with a git version). Unpause and trigger `railway_example_fanout`; 12 mapped tasks run on the worker.
- [ ] Task logs open in the UI while running (worker log server via private domain) and after completion (from the Bucket, `task-logs/` prefix visible in the Bucket file browser).
- [ ] Push a change to the DAG repo → new DAG version within ~2 minutes.
- [ ] Redeploy all services: users, connections, DAG runs and logs persist.
- [ ] Scale `airflow-worker` to 2 replicas; both pick up tasks.

## Open questions

- Not deployed end-to-end here. The `AIRFLOW_CONN_RAILWAY_BUCKET` JSON (virtual-hosted addressing for Railway/Tigris buckets) and the dual-stack uvicorn bind need a first-deploy check.
- The default `AIRFLOW_DAGS_GIT_URL` points at the template monorepo placeholder; it must be public at the final location before publishing (or be emptied to use the baked-in examples).
- With several `airflow-worker` replicas, live logs of a *running* task may be requested from a different replica (all share one private DNS name). Finished-task logs come from the Bucket and are unaffected.
- Flower (optional upstream profile) is not included; add `celery flower` as a service if Celery-level monitoring is wanted.

# Apache Airflow 3 for Railway: one image, one role per Railway service.
# The role is chosen by the service's start command:
#   /opt/railway/bin/railway-airflow <init|api-server|scheduler|dag-processor|triggerer|worker>
#
# Pin: every Airflow service builds from this file, so this FROM line is the
# single place that sets the Airflow version for the whole stack.
FROM apache/airflow:3.3.2

USER root
COPY --chown=50000:0 railway_airflow/ /opt/railway/railway_airflow/
COPY --chown=50000:0 bin/ /opt/railway/bin/
# Example DAGs, used when no git repository is configured (dags-folder bundle).
COPY --chown=50000:0 dags/ /opt/airflow/dags/
RUN chmod 0755 /opt/railway/bin/railway-airflow
USER 50000

ENV PYTHONPATH=/opt/railway \
    AIRFLOW__CORE__EXECUTOR=CeleryExecutor \
    AIRFLOW__CORE__AUTH_MANAGER=airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager \
    AIRFLOW__CORE__LOAD_EXAMPLES=False \
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=True \
    AIRFLOW__CORE__HOSTNAME_CALLABLE=railway_airflow.hostname.private_domain \
    AIRFLOW__LOGGING__DELETE_LOCAL_LOGS=True \
    AIRFLOW__SCHEDULER__ENABLE_HEALTH_CHECK=True

# Fail the build on syntax errors in the files added above.
RUN python -m compileall -q /opt/railway/railway_airflow /opt/airflow/dags \
 && bash -n /opt/railway/bin/railway-airflow

"""Hostname reported by Airflow components on Railway.

Airflow stores the hostname of the machine that ran a task and later fetches
live logs from ``http://<hostname>:8793``. Container hostnames on Railway are
random and not resolvable by other services, so report the service's private
DNS name (``<service>.railway.internal``) instead.
"""

from __future__ import annotations

import os
import socket


def private_domain() -> str:
    """Return RAILWAY_PRIVATE_DOMAIN, falling back to the container FQDN."""
    domain = os.environ.get("RAILWAY_PRIVATE_DOMAIN", "").strip()
    return domain or socket.getfqdn()

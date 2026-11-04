"""Prometheus metrics: one registry per process, the default one, with the runtime collectors (process,
garbage collector). Each component registers its own metrics on it and serves them on `/metrics`.

One process per container: scale out with more instances, not more processes. Counters stay accurate without
the multiprocess mode of `prometheus_client`.
"""

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest


def exposition() -> tuple[bytes, str]:
    """Every metric of the process, in the Prometheus text format, and its content type."""
    return generate_latest(), CONTENT_TYPE_LATEST

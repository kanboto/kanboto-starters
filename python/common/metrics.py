"""Prometheus metrics: the runtime collectors (process, garbage collector) on the default registry, and one
registry per component package for its own metrics, so that several components, even two copies of one
module, live in one process (the tests) without their metric names colliding. Each component serves the
runtime metrics and its own on `/metrics`.

One process per container: scale out with more instances, not more processes. Counters stay accurate without
the multiprocess mode of `prometheus_client`.
"""

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest


def exposition(registry: CollectorRegistry) -> tuple[bytes, str]:
    """The runtime metrics and those of `registry`, in the Prometheus text format, and its content type."""
    return generate_latest(REGISTRY) + generate_latest(registry), CONTENT_TYPE_LATEST

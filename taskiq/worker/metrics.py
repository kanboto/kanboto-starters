"""Prometheus metrics of the worker: task executions, on the registry of this package, served with the
runtime metrics (`common.metrics`) by `health.py`. One process per container: scale out with more instances.
"""

from prometheus_client import CollectorRegistry, Counter, Histogram

REGISTRY = CollectorRegistry()
TASKS = Counter(
    "tasks_total", "Task executions (each attempt counts), by outcome", ["task", "status"], registry=REGISTRY
)
# Tasks last from milliseconds to TASK_TIMEOUT_S (60 by default): the default buckets stop at 10 s.
BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300)
DURATION = Histogram(
    "task_duration_seconds", "Task execution duration", ["task"], buckets=BUCKETS, registry=REGISTRY
)
DEAD_LETTERS = Counter(
    "tasks_dead_lettered_total",
    "Messages dead-lettered: failed every attempt, invalid, unreadable or for an unknown task",
    ["task"],
    registry=REGISTRY,
)
# Example business metric: replace it with your domain's.
ITEMS_PROCESSED = Counter("items_processed_total", "Items processed", registry=REGISTRY)


def observe(task: str, status: str, duration: float) -> None:
    DURATION.labels(task).observe(duration)
    TASKS.labels(task, status).inc()

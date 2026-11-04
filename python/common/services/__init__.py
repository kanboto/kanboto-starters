"""Business rules, written once and called by every component: an API handler, a task, a command. A service
takes its session as an argument and knows nothing of HTTP or of the task queue."""

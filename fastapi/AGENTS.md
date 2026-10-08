# AGENTS.md

<!-- kanboto:start -->
## Règles Kanboto (stack FastAPI)

Section tenue par Kanboto : ne pas la modifier à la main, Kanboto la met à jour par PR. Ces règles sont
vérifiées par la CI (`kanboto-ci-*`) ; une PR qui les enfreint ne passe pas.

### Exécution (Kubernetes)

- Configuration par variables d'environnement uniquement, chacune listée dans `.env.example` ; aucune
  valeur en dur, aucun fichier de configuration dans l'image. Les adresses des autres services arrivent par
  des variables explicites (`BILLING_API_URL`), jamais par les variables de découverte de Kubernetes.
- Sans état : rien n'est écrit hors de `/tmp` (l'image tourne en lecture seule) ; sessions, fichiers et
  caches vont dans un service externe. Plusieurs réplicas tournent côte à côte.
- Non bloquant : pilotes async (base, HTTP), aucun appel bloquant dans une fonction `async`, un délai
  maximal sur chaque appel sortant ; un travail CPU long part dans un worker par une file.
- `GET /healthz` (vivant), `GET /readyz` (dépendances joignables, 503 pendant l'arrêt) et `GET /metrics`
  (Prometheus) restent à la racine, sur `PORT` : ils ne sont jamais exposés publiquement.
- Arrêt propre sur `SIGTERM` dans `SHUTDOWN_TIMEOUT_S` : le travail en cours se termine.
- Logs en JSON sur la sortie standard, une ligne par événement.
- Image multi-stage, utilisateur non-root, base épinglée par digest ; les migrations passent par
  `python -m app migrate`, jamais au démarrage du service.

### API

- Routes publiques sous `/api/v<N>/`, internes sous `/internal/v<N>/` ; seule la version majeure est dans
  le chemin.
- Un changement compatible (champ, paramètre facultatif ou endpoint ajouté) reste dans la version. Un
  changement cassant ouvre `/api/v<N+1>/` ; l'ancienne version reste servie, marquée `deprecated` avec une
  date de retrait (en-têtes `Deprecation` et `Sunset`). Rien n'est cassé dans une version déjà publiée.
- La spec `openapi/public.yaml` suit le code : `python -m app openapi > openapi/public.yaml`.
- Erreurs au format RFC 9457 (`application/problem+json`) ; dates ISO 8601 en UTC ; pagination par
  curseur (`limit`, `cursor`, réponse `items` et `next_cursor`) ; ressources au pluriel.
- Un `POST` qui crée ou déclenche un effet exige `Idempotency-Key` (voir `app/idempotency.py`).

### Commandes

- Installer : `uv sync`
- Lint, format, typage : `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy .`
- Tests : `uv run pytest`
<!-- kanboto:end -->

## Ce starter

- `app/main.py` assemble l'application ; `app/api/v1/` porte la version 1 de l'API. `items` est une
  ressource d'exemple : la remplacer par celles du domaine en gardant ses conventions.
- `app/health.py`, `app/metrics.py`, `app/logs.py`, `app/errors.py`, `app/idempotency.py` et
  `app/pagination.py` remplissent les contrats ; les garder.
- Les tests utilisent SQLite, créée par les migrations à chaque test ; la prod utilise PostgreSQL.

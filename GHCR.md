# Mirrored images

Copies of the images used by Kanboto's CI kits and starters, so that CI does not depend on upstream
registries' rate limits (Docker Hub's anonymous pulls in particular). Refreshed nightly by
[`mirror-images.yml`](.github/workflows/mirror-images.yml): tools at their latest stable release
(tag `stable`, plus the version tag), versioned images under their upstream tag. Manifests are copied
intact, so each digest is the upstream one. Since: the date this digest was first mirrored.

| Source | Mirror | Digest | Since |
|---|---|---|---|
| `ghcr.io/hadolint/hadolint:v2.15.1` | `ghcr.io/kanboto/hadolint:stable`, `v2.15.1` | `sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d` | 2026-10-09 |
| `ghcr.io/aquasecurity/trivy:0.76.0` | `ghcr.io/kanboto/trivy:stable`, `0.76.0` | `sha256:2416d1f74045b57274df1a340eee6b510cacd73c66a6ccb8da092b117eb7d222` | 2026-10-15 |
| `ghcr.io/aquasecurity/trivy-db:2` | `ghcr.io/kanboto/trivy-db:2` | `sha256:2bfa4ccf12f3243cd7cef40b98465bd2dfd6926816d0210c785ea36c4e94959c` | 2026-10-20 |
| `ghcr.io/aquasecurity/trivy-checks:2` | `ghcr.io/kanboto/trivy-checks:2` | `sha256:b0e12d009b01dcc8ca2ebbc199b9caf3922491978d21c17b61c1d7f6dc75220b` | 2026-10-15 |
| `tufin/oasdiff:v1.34.0` | `ghcr.io/kanboto/oasdiff:stable`, `v1.34.0` | `sha256:dd742562c1f3146f6e2a80bc01951cc87d15a249ac2aca05665339e30cf03620` | 2026-10-19 |
| `postgres:17-alpine` | `ghcr.io/kanboto/postgres:17-alpine` | `sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24` | 2026-10-09 |
| `node:24-trixie-slim` | `ghcr.io/kanboto/node:24-trixie-slim` | `sha256:7f486cabe892bff8fef04c0f7da8dba84a560be3e4e2740b7a86afc57ebec315` | 2026-10-15 |

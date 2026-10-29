# Mirrored images

Copies of the images used by Kanboto's CI kits and starters, so that CI does not depend on upstream
registries' rate limits (Docker Hub's anonymous pulls in particular). Refreshed nightly by
[`mirror-images.yml`](.github/workflows/mirror-images.yml): tools at their latest stable release
(tag `stable`, plus the version tag), versioned images under their upstream tag. Manifests are copied
intact, so each digest is the upstream one. Since: the date this digest was first mirrored.

| Source | Mirror | Digest | Since |
|---|---|---|---|
| `ghcr.io/hadolint/hadolint:v2.15.1` | `ghcr.io/kanboto/hadolint:stable`, `v2.15.1` | `sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d` | 2026-10-09 |
| `ghcr.io/aquasecurity/trivy:0.76.1` | `ghcr.io/kanboto/trivy:stable`, `0.76.1` | `sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c` | 2026-10-22 |
| `ghcr.io/aquasecurity/trivy-db:2` | `ghcr.io/kanboto/trivy-db:2` | `sha256:19b5d8a057520ec1b57fb0a1b5f0a1e11f856df2e8e83a3aa1b467093d0b094f` | 2026-10-29 |
| `ghcr.io/aquasecurity/trivy-checks:2` | `ghcr.io/kanboto/trivy-checks:2` | `sha256:b0e12d009b01dcc8ca2ebbc199b9caf3922491978d21c17b61c1d7f6dc75220b` | 2026-10-15 |
| `tufin/oasdiff:v1.35.0` | `ghcr.io/kanboto/oasdiff:stable`, `v1.35.0` | `sha256:82b1840a77335562bb11ce95f77ad31745a0c6f3a770929333ed1c5ef466e400` | 2026-10-29 |
| `postgres:17-alpine` | `ghcr.io/kanboto/postgres:17-alpine` | `sha256:266d3c257594e195b309ae9d1805e54c788f1d7b375f56bf6c367aac6c917e7b` | 2026-10-26 |
| `node:24-trixie-slim` | `ghcr.io/kanboto/node:24-trixie-slim` | `sha256:54f84b4cf8432b21aaffd5d3ce8d41e12cea0d10d33c09d2f3c9879d49d6b446` | 2026-10-29 |

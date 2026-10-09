# Production image: multi-stage, the built server only, non-root user, runtime image pinned by digest.
# Build stage from Kanboto's mirror of Docker Hub's node image (digest recorded in GHCR.md).
# Distroless runtime: Node.js 24, no shell, no package manager.
FROM ghcr.io/kanboto/node:24-trixie-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
# Dependencies' install scripts stay off (see `allowScripts`); `nuxt build` prepares the project itself.
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY . .
RUN npm run build

# `.output` is self-contained: the server and the few dependencies it uses, traced by Nitro.
FROM gcr.io/distroless/nodejs24-debian13:nonroot@sha256:9eeb7f5887d0e239e78264b06f7f11d2e14be534050481803a9e4728fcdd278e
WORKDIR /app
COPY --from=build --chown=root:root /app/.output ./.output
ENV NODE_ENV=production PORT=8080
# The `nonroot` user of distroless images.
USER 65532
EXPOSE 8080
# The image's entrypoint is `node`.
CMD [".output/server/index.mjs"]

# Production image: multi-stage, the built server only, non-root user, base images pinned by digest.
# Distroless runtime: Node.js 24, no shell, no package manager.
FROM node:24-trixie-slim@sha256:173f125896c3b47ddf056734c7ea789d04595a6a08769a8f78e0df642781fb66 AS build
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

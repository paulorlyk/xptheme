# syntax=docker/dockerfile:1
# Builds XP-Luna-for-Mint and XP-Classic-for-Mint in a clean Debian. Used by docker-build.sh;
# see there. The build context is the repository root (.dockerignore lets only the themes'
# sources through).
#
# Run with `docker build --target export-luna|export-classic --output type=local,dest=DIR`:
# those stages are FROM scratch and hold only the built theme, which BuildKit writes to DIR.
# No image or container is made. Each theme's Microsoft input comes from a named build context
# ("msstyles": luna.msstyles, "scheme": Windows Classic.theme) and is only bind-mounted while
# that theme builds, so it is never in a layer. BuildKit builds only the stages the target
# needs, so each target needs only its own context.
FROM debian:trixie-slim AS base

ENV DEBIAN_FRONTEND=noninteractive

# python3-venv: build.sh's venv (Pillow); fontconfig + a font: the theme chooser thumbnails'
# labels (Luna's gen_assets.py asks fc-match for Tahoma and gets DejaVu here; Classic's
# gen_thumbnail.py asks for DejaVu Sans only).
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        python3 \
        python3-venv \
        fontconfig \
        fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

# Both themes import from shared/, next to them as in the repo.
COPY shared/tools/ /src/shared/tools/

# build.sh creates build/venv only if it's missing, so make it here: the theme builds
# themselves then need no network.
FROM base AS luna
WORKDIR /src/xp-luna-for-mint
RUN python3 -m venv build/venv && build/venv/bin/pip install -q --no-cache-dir pillow
COPY xp-luna-for-mint/build.sh ./
COPY xp-luna-for-mint/tools/ tools/
ARG XP_BASE=Adwaita
ARG XP_NO_BORDERS=
RUN --mount=type=bind,from=msstyles,target=/msstyles \
    XP_MSSTYLES=/msstyles/luna.msstyles XP_BASE="$XP_BASE" XP_NO_BORDERS="$XP_NO_BORDERS" ./build.sh

FROM base AS classic
WORKDIR /src/xp-classic-for-mint
RUN python3 -m venv build/venv && build/venv/bin/pip install -q --no-cache-dir pillow
COPY xp-classic-for-mint/build.sh ./
COPY xp-classic-for-mint/tools/ tools/
ARG XP_BASE=Adwaita
ARG XP_NO_BORDERS=
RUN --mount=type=bind,from=scheme,target=/scheme \
    XP_SCHEME=/scheme/scheme.theme XP_BASE="$XP_BASE" XP_NO_BORDERS="$XP_NO_BORDERS" ./build.sh

FROM scratch AS export-luna
COPY --from=luna /src/xp-luna-for-mint/build/XP-Luna-for-Mint /XP-Luna-for-Mint

FROM scratch AS export-classic
COPY --from=classic /src/xp-classic-for-mint/build/XP-Classic-for-Mint /XP-Classic-for-Mint

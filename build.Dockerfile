# syntax=docker/dockerfile:1
# Builds XP-Luna-for-Mint in a clean Debian. Used by docker-build.sh; see there. The build
# context is the repository root (.dockerignore lets only the theme's sources through).
#
# Run with `docker build --output type=local,dest=DIR`: the final stage is FROM scratch and
# holds only the built theme, which BuildKit writes to DIR. No image or container is made.
# luna.msstyles comes from the named build context "msstyles" and is only bind-mounted
# while the theme builds, so it is never in a layer.
FROM debian:trixie-slim AS build

ENV DEBIAN_FRONTEND=noninteractive

# python3-venv: build.sh's venv (Pillow); fontconfig + a font: gen_assets.py asks fc-match
# for Tahoma to label the theme chooser thumbnail.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        python3 \
        python3-venv \
        fontconfig \
        fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /theme

# build.sh creates build/venv only if it's missing, so make it here: the theme build itself
# then needs no network.
RUN python3 -m venv build/venv && build/venv/bin/pip install -q --no-cache-dir pillow

COPY xp-luna-for-mint/build.sh ./
COPY xp-luna-for-mint/tools/ tools/

ARG XP_BASE=Adwaita
RUN --mount=type=bind,from=msstyles,target=/msstyles \
    XP_MSSTYLES=/msstyles/luna.msstyles XP_BASE="$XP_BASE" ./build.sh

FROM scratch AS export
COPY --from=build /theme/build/XP-Luna-for-Mint /XP-Luna-for-Mint

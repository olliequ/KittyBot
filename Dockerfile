FROM python:3.11
ARG UID=1001
ARG GID=1001
RUN apt-get update \
    && apt-get install -y --no-install-recommends libfreetype6-dev libxft-dev fortunes \
    && pip install --no-cache-dir uv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home
COPY uv.lock pyproject.toml ./
RUN uv sync --compile-bytecode --locked --no-dev \
    && mkdir -p /data /data/memory /home/.cache /home/.config
COPY --chown=$UID:$GID . /home/
ENV HOME=/home
RUN chown -R $UID:$GID /data /home/.cache /home/.config
ENV FORTUNE_DIRECTORY=/usr/share/games/fortunes
ENV KITTY_DB=/data/persist.sqlite
ENV KITTY_MEMORY_DIR=/data/memory
USER $UID
CMD ["uv", "run", "--no-sync", "bot.py"]

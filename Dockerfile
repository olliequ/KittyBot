FROM python:3.11
ARG UID=1001
ARG GID=1001
RUN apt update -y && apt upgrade -y \
    && apt install libfreetype6-dev libxft-dev fortunes -y \
    && pip install uv

WORKDIR /home
COPY uv.lock pyproject.toml init-lm.py .
RUN uv sync --compile-bytecode --locked --no-dev \
    && uv run --no-sync init-lm.py \
    && mkdir /data /home/.cache /home/.config \
    && chown -R $UID:$GID /data /home/.cache /home/.config

COPY --chown=$UID:$GID . /home/
ENV HOME=/home
ENV FORTUNE_DIRECTORY=/usr/share/games/fortunes
ENV KITTY_DB=/data/persist.sqlite
USER $UID
CMD ["uv", "run", "--no-sync", "bot.py"]

FROM python:3.11
ARG UID=1001
ARG GID=1001
RUN apt update -y && apt upgrade -y \
    && apt install libfreetype6-dev libxft-dev fortunes -y \
    && pip install uv

WORKDIR /home
COPY uv.lock pyproject.toml init-lm.py ./
RUN uv sync --compile-bytecode --locked --no-dev \
    && mkdir /data /home/.cache /home/.config /home/.ollama 
RUN curl -fsSL https://ollama.com/install.sh | sh
COPY --chown=$UID:$GID . /home/
ENV HOME=/home
RUN uv run --no-sync init-lm.py
RUN ollama serve & sleep 5 && ollama pull qwen3:0.6b && ollama pull qwen3:1.7b
RUN chown -R $UID:$GID /data /home/.cache /home/.config /home/.ollama
ENV FORTUNE_DIRECTORY=/usr/share/games/fortunes
ENV KITTY_DB=/data/persist.sqlite
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_PORT=11434
USER $UID
CMD ["bash", "-c", "ollama serve & sleep 2 && exec uv run --no-sync bot.py"]

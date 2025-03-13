FROM python:3.11
ARG UID=1001
ARG GID=1001
RUN apt update -y && apt upgrade -y \
    && apt install libfreetype6-dev libxft-dev fortunes -y
RUN pip install uv

COPY requirements.txt /home
RUN uv pip install --system -r /home/requirements.txt
COPY --chown=$UID:$GID . /home/
RUN mkdir /data  && chown -R $UID:$GID /data && mkdir /home/.cache && chown -R $UID:$GID /home/.cache 
RUN python -c "import languagemodels as lm;lm.config['instruct_model']='Qwen2.5-0.5B-Instruct';lm.do('testing')"
ENV HOME /home
ENV FORTUNE_DIRECTORY /usr/share/games/fortunes
ENV KITTY_DB /data/persist.sqlite
WORKDIR /home
USER $UID
CMD ["python", "bot.py"]

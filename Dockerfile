FROM python:3.8.10
RUN apt update -y && apt upgrade -y \
    && apt install libfreetype6-dev libxft-dev fortune -y
COPY . /home/
RUN pip install -r /home/requirements.txt
RUN mkdir kitty-db && chown -R 1001 /home
ENV HOME /home
ENV FORTUNE_DIRECTORY /usr/share/games/fortunes
ENV KITTY_DB /home/kitty-db/persist.sqlite
WORKDIR /home
USER 1001

CMD ["python", "bot.py"]

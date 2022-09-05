FROM python:3.10
RUN apt update -y && apt upgrade -y \
    && apt install libfreetype6-dev libxft-dev fortune -y
COPY . /home/
RUN pip install -r /home/requirements.txt
ENV HOME /home
ENV FORTUNE_DIRECTORY /usr/share/games/fortunes
ENV KITTY_DB /home/kitty-db/persist.sqlite
WORKDIR /home
RUN mkdir kitty-db && chown -R 1001 /home
USER 1001
CMD ["python", "bot.py"]

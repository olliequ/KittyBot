FROM python:3.8.10
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install libfreetype6-dev libxft-dev fortune -y
COPY . /home/
RUN pip install -r /home/requirements.txt
WORKDIR /home
ENV HOME /home
ENV FORTUNE_DIRECTORY=/usr/share/games/fortunes
USER 1001
CMD ["python", "bot.py"]

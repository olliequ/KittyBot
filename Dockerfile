FROM python:3.8.10
COPY requirements.txt /home/
RUN pip install -r /home/requirements.txt
COPY . /home/
RUN rm /home/requirements.txt
WORKDIR /home
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install libfreetype6-dev libxft-dev fortune -y
ENV HOME /home
ENV FORTUNE_DIRECTORY=/usr/share/games/fortunes
EXPOSE 443
USER 1001
CMD ["python", "bot.py"]

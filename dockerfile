FROM python:3.9.7-slim-buster
ENV TOKEN=${TOKEN}
WORKDIR /whale_sniper
COPY . /whale_sniper
RUN pip install -r requirements.txt
CMD [ "python", "./bot.py" ]
FROM python:3
FROM gorialis/discord.py

RUN mkdir -p /usr/src/bot 
RUN pip install apscheduler
WORKDIR /usr/src/bot

COPY . .

CMD [ "python3", "-u", "bot.py" ]

# Base image for build
FROM python:3.7.2-alpine3.7
WORKDIR /app

RUN apk add --update python3 \
    python3-dev \
    py-pip \
    build-base

RUN pip3 install --upgrade pip

# install packages
RUN pip3 install beautifulsoup4
RUN pip3 install python-telegram-bot
RUN pip3 install requests

# copy project files
COPY . ./

ENTRYPOINT ["python3", "bot.py"]
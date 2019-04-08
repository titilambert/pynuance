FROM ubuntu:17.04

RUN apt-get update && apt-get install -y python3-pip libspeex-dev swig libpulse-dev libspeexdsp-dev portaudio19-dev libsamplerate0-dev libopus-dev wget unzip

RUN mkdir pynuance
WORKDIR /pynuance

RUN wget https://github.com/titilambert/pynuance/archive/aiohttp2.zip
RUN unzip aiohttp2.zip

RUN pip3 install numpy


WORKDIR /pynuance/pynuance-aiohttp2
RUN pip3 install -r requirements.txt


RUN python3 setup.py develop

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

ADD credentials.json /pynuance/pynuance-aiohttp2

RUN pynuance nlu -c credentials.json -l fr_FR text -T "Heure"

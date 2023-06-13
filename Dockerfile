FROM python:3.11.4
MAINTAINER michael weinstein <michael.weinstein@tecan.com>

USER root

ENV DEBIAN_FRONTEND noninteractive

RUN apt update
RUN apt install -y samtools=1.11-1
RUN apt clean
RUN apt purge
RUN rm -rf /var/lib/apt/lists/* /tmp/*

RUN mkdir /opt/bedFastaValidation
COPY *.py /opt/bedFastaValidation/
COPY fbvsupport /opt/bedFastaValidation/fbvsupport

RUN useradd -ms /bin/bash swisscow

USER swisscow


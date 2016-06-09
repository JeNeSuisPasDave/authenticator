# Using a base Ubuntu 14.04 that has the latest updates already
#
# Base images can be found here: https://hub.docker.com/_/ubuntu/
# Ubuntu 14.04 LTS (Trusty Tahr) is supported through 2019.
# Ubuntu 16.04 LTS (Xenial Xerus) has just been released and probably should
#   not be used yet (because dependent software may need to be updated and
#   made compatible).
#
FROM ubuntu:14.04.4
MAINTAINER Dave Hein <dhein@acm.org>

# Setting this environment variable prevents errors during package installs
# that look like:
#
# debconf: unable to initialize frontend: Dialog
# debconf: (TERM is not set, so the dialog frontend is not usable.)
# debconf: falling back to frontend: Readline
#
# As per: http://stackoverflow.com/a/35976127/1392864
#
ARG DEBIAN_FRONTEND=noninteractive

# Update apt package info and upgrade installed packages (base image
# has some packages installed)
#
# Install some basic package fetching tools
#
ENV FETCH_REFRESHED_AT 2016-06-08T05:25-0500
RUN apt-get update && apt-get -y upgrade \
	apt-get install -yqq software-properties-common python-software-properties && \
	apt-get -yqq install wget

# Install Python 3.5
#
ENV PYTHON35_REFRESHED_AT 2016-06-08T05:25-0500
RUN add-apt-repository ppa:fkrull/deadsnakes && \
	apt-get update
RUN apt-get install -yqq python3.5
RUN apt-get install -yqq python3.5-dev
RUN apt-get install -yqq libncurses5-dev
RUN apt-get install -yqq python3.5-venv

# Install pip & setuptools
#
ENV PIP3_REFRESHED_AT 2016-06-08T05:47-0500
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3 get-pip.py
RUN pip3 install setuptools --upgrade

# Install git
#
ENV GIT_REFRESHED_AT 2016-06-08T05:47-0500
RUN apt-get install -yqq git-core

# Install gcc
#
ENV GCC_REFRESHED_AT 2016-06-08T05:47-0500
RUN apt-get install -yqq \
	autoconf \
	automake \
	g++ \
	gcc \
	libffi-dev \
	libssl-dev \
	make \
	patch

# Local stuff
ENV LOCALSTUFF_REFRESHED_AT 2016-06-08T06:07-0500
COPY establish-dev.sh /root/trash/
WORKDIR /root/trash

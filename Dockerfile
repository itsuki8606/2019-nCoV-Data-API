FROM ubuntu:latest
LABEL maintainer nCoV
ENV PYTHONUNBUFFERED 1
WORKDIR /nCoV_2019_project/
COPY . /nCoV_2019_project/
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN apt-get update
RUN apt-get install sudo
RUN sudo apt-get install -y python3.6
RUN sudo apt-get install -y python3-pip
RUN pip3 install pipenv
RUN pipenv install
CMD pipenv run python3 manage.py runserver 0:3000
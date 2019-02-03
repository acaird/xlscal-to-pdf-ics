FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN pip install xlrd
RUN pip install python-dateutil

COPY ./app /app
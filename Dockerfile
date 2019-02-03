FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN pip install xlrd
RUN pip install python-dateutil
RUN pip install reportlab
RUN pip install icalendar

COPY ./app /app
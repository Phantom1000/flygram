FROM python:latest

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install gunicorn cryptography

COPY boot.sh ./
COPY celery.sh ./
RUN chmod a+x *.sh

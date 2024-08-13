#!/bin/sh

export FLASK_APP=main

flask db init

flask db migrate

flask db upgrade

exec gunicorn -b :5000 --worker-class eventlet -w 1 --access-logfile - --error-logfile - main:app
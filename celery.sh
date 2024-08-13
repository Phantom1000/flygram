#!/bin/bash

# shellcheck disable=SC2164
cd src

if [[ "${1}" == "celery" ]]; then
  celery --app=main.celery_app worker -l INFO
elif [[ "${1}" == "flower" ]]; then
  celery --app=main.celery_app flower
fi

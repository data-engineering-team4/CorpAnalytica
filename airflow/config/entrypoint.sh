#!/usr/bin/env bash

TRY_LOOP="20"

: "${REDIS_HOST:="redis"}"
: "${REDIS_PORT:="6379"}"

: "${POSTGRES_HOST:="postgres"}"
: "${POSTGRES_PORT:="5432"}"

wait_for_port() {
  local name="$1" host="$2" port="$3"
  local j=0
  while ! nc -z "$host" "$port" >/dev/null 2>&1 < /dev/null; do
    j=$((j+1))
    if [ $j -ge $TRY_LOOP ]; then
      echo >&2 "$(date) - $host:$port still not reachable, giving up"
      exit 1
    fi
    echo "$(date) - waiting for $name... $j/$TRY_LOOP"
    sleep 5
  done
}

CELERY_RESULT_BACKEND_CONNECTION="db+postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
CELERY_REDIS_CONNECTION="redis://${REDIS_HOST}:${REDIS_PORT}"
sed -e "s&{{CELERY_REDIS_CONNECTION}}&${CELERY_REDIS_CONNECTION}&g" \
  -e "s&{{CELERY_RESULT_BACKEND_CONNECTION}}&${CELERY_RESULT_BACKEND_CONNECTION}&g" \
  airflow.cfg > seedtest.cfg && mv seedtest.cfg airflow.cfg

wait_for_port "Postgres" "$POSTGRES_HOST" "$POSTGRES_PORT"

wait_for_port "Redis" "$REDIS_HOST" "$REDIS_PORT"

case "$1" in
  webserver)
    airflow db init
    sleep 5
    airflow users create \
    --username admin \
    --firstname firstname \
    --lastname lastname \
    --role Admin \
    --email admin@example.org \
    --password admin 
    sleep 5
    exec airflow webserver
    ;;
  worker)
    sleep 15
    exec airflow celery "$@"
    ;;
  scheduler)
    sleep 15
    exec airflow "$@"
    ;;
  flower)
    echo "flower"
    sleep 15
    exec airflow celery "$@"
    ;;
  version)
    exec airflow "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
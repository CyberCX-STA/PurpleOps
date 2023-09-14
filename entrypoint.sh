#!/bin/sh

echo "Waiting for Mongo..."

while ! nc -z "$MONGO_HOST" 27017; do
    sleep 0.1
    done

python seeder.py

exec "$@"

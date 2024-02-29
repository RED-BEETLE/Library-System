#!/bin/bash

DB=bookManager
USER=a
PASSWORD=1234
FLASK_APP=app/app.py
FLASK_ENV=development

export PGPASSWORD="$PASSWORD"

dropdb -U "$USER" $DB
createdb -U "$USER" $DB

psql -U "$USER" $DB -f sql/tables.sql
psql -U "$USER" $DB -f sql/insert.sql
psql -U "$USER" $DB -f sql/functions.sql

unset PGPASSWORD

python3 simulate.py

export FLASK_APP="$FLASK_APP"
export FLASK_ENV="$FLASK_ENV"
flask run
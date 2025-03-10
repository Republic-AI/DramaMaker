#!/bin/bash

# -------------------------------------------------------------
# Script Name: import_aitown.sh
# Description: Imports tmpAITown_backup.sql into "aitown" database
# Usage:       ./import_aitown.sh
# -------------------------------------------------------------

# MySQL connection info
HOST="localhost"
USER="root"
PASSWORD="Hupidan98"
DATABASE="aitown"

# Path to the SQL file
SQL_FILE="/Users/jackhan/Desktop/AITown/satoshiLive/memelive/MultiAgent-Framwork/tmpAITown_backup.sql"

# 1) Check if the SQL file exists
if [ ! -f "$SQL_FILE" ]; then
    echo "Error: File $SQL_FILE does not exist."
    exit 1
fi

# 2) Create the database if it doesn't already exist
echo "Ensuring database '$DATABASE' exists..."
mysql -h "$HOST" -u "$USER" -p"$PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$DATABASE\`;"

# 3) Import the SQL file
echo "Importing $SQL_FILE into database '$DATABASE'..."
mysql -h "$HOST" -u "$USER" -p"$PASSWORD" "$DATABASE" < "$SQL_FILE"

# 4) Check for errors
if [ $? -eq 0 ]; then
    echo "Import successful!"
else
    echo "Import encountered an error."
    exit 1
fi
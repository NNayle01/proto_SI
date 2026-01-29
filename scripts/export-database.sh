#!/bin/bash

# Script to export the Dolibarr database
# This creates a complete backup of the database including all products, configurations, and modules

echo "📦 Exporting Dolibarr database..."

# Database credentials (should match docker-compose.yml)
DB_CONTAINER="dolibarr_db"
DB_NAME="dolibarr"
DB_USER="dolibarr"
DB_PASSWORD="dolibarrpass"

# Output file
OUTPUT_FILE="./database/init-dolibarr.sql"

# Check if database container is running
if ! docker ps | grep -q $DB_CONTAINER; then
    echo "❌ Error: Database container '$DB_CONTAINER' is not running"
    echo "Please start the containers with: docker compose up -d"
    exit 1
fi

# Export database
echo "Exporting database to $OUTPUT_FILE..."
docker exec $DB_CONTAINER mysqldump \
    -u $DB_USER \
    -p$DB_PASSWORD \
    $DB_NAME > $OUTPUT_FILE

# Check if export was successful
if [ $? -eq 0 ]; then
    echo "✅ Database exported successfully!"
    echo "📊 File size: $(du -h $OUTPUT_FILE | cut -f1)"
    echo ""
    echo "The database dump has been saved to: $OUTPUT_FILE"
    echo "This file will be automatically imported when new users run 'docker compose up' for the first time."
else
    echo "❌ Error: Database export failed"
    exit 1
fi

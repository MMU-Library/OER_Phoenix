#!/bin/sh

# Simple database check and creation
if [ -n "$DB_HOST" ]; then
    echo "Waiting for database at $DB_HOST:$DB_PORT..."
    while ! nc -z $DB_HOST $DB_PORT; do sleep 0.5; done
    echo "Database ready!"
fi

# Create the database if it doesn't exist
echo "Checking if database exists and creating if necessary..."
python manage.py shell -c "
from django.conf import settings;
import psycopg2;
try:
    conn = psycopg2.connect(
        dbname='oer_rebirth',
        user='$DB_USER',
        password='$DB_PASSWORD',
        host='$DB_HOST'
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(\"SELECT 1 FROM pg_database WHERE datname='%s'\" % settings.DATABASES['default']['NAME'])
    exists = cursor.fetchone()
    if not exists:
        cursor.execute(\"CREATE DATABASE %s WITH ENCODING 'UTF8' TEMPLATE template0;\" % settings.DATABASES['default']['NAME'])
    cursor.close()
    conn.close()
except Exception as e:
    print('Error creating database:', str(e))
"

# Run migrations
echo "Running migrations..."
python manage.py makemigrations resources
python manage.py migrate

# Create superuser non-interactively
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
    print('Superuser created')
else:
    print('Superuser already exists')
"

# Run the application
echo "Starting Django server..."
exec "$@"
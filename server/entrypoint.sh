#!/bin/bash
set -e  # Прерывать выполнение при любой ошибке

# Выполнить миграции
echo "Running Alembic migrations..."
alembic upgrade head

# Запустить приложение
echo "Starting the application..."
#exec "$@" передает все аргументы из CMD (в моем случае uvicorn main:app --host=0.0.0.0 --port=5000 --reload) в качестве команды для выполнения.
exec "$@"

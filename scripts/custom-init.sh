#!/bin/bash
set -e  # Завершить выполнение скрипта при любой ошибке
# Проверяем, задана ли переменная TEST_DB
if [ -n "$TEST_DB" ]; then
    echo "Переменная TEST_DB задана: $TEST_DB"
    echo "Создаю базу данных: $TEST_DB"

    # Выполняем SQL-команду для создания базы данных
    echo "CREATE DATABASE $TEST_DB;" | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
else
    echo "Переменная окружения TEST_DB не задана. Пропускаю создание тестовой базы данных."
fi

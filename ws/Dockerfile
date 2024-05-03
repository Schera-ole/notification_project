# Используем базовый образ Python
FROM python:3.11

# Устанавливаем зависимости
RUN pip install websockets

# Копируем исходный код в образ
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app
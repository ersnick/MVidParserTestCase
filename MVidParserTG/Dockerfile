# Используем базовый образ с Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы программы в контейнер
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Команда для запуска программы
CMD ["python", "main.py"]

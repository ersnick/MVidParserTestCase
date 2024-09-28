# Используем базовый образ с Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы программы в контейнер
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт приложения
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
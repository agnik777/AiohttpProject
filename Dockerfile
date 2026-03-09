
FROM python:3.13-alpine

# Установка завсисимостей для psycopg2
RUN apk add --no-cache gcc musl-dev linux-headers

WORKDIR app

# Установка завсисимостей из requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

CMD ["python", "declarations.py"]

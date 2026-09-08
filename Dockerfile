FROM python:3.14-slim

WORKDIR /app

# Erst nur die Abhaengigkeiten: diese Schicht bleibt im Cache,
# solange sich requirements.txt nicht aendert.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dann der eigentliche Code.
COPY . .

# 0.0.0.0 statt 127.0.0.1: sonst horcht der Dienst nur im Container
# und die Portweitergabe von aussen laeuft ins Leere.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
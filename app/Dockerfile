FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Create a non-root user and switch to it
RUN useradd -ms /bin/sh appuser
USER appuser

CMD ["python", "app.py"]
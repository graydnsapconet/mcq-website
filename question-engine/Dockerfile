FROM python:3.11-slim

WORKDIR /question-engine

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user and switch to it
RUN useradd -ms /bin/sh appuser2
USER appuser2

CMD ["python", "qe-app.py"]
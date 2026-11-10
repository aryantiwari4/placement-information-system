FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

EXPOSE 5000

# Run with Gunicorn WSGI server for production
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]


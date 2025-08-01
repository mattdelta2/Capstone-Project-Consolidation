FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install C build tools, MySQL client headers, and pkg-config
RUN apt-get update \
 && apt-get install -y \
      build-essential \
      default-libmysqlclient-dev \
      pkg-config \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy application code
COPY . .



EXPOSE 8000

CMD ["uvicorn", "news_portal.asgi:application", "--host", "0.0.0.0", "--port", "8000"]

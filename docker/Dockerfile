FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Flask requirements from the docker folder
COPY docker/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (Assuming build context is the repository root)
COPY spatialmedia /app/spatialmedia
COPY docker/app.py /app/app.py
COPY docker/templates /app/templates
COPY docker/static /app/static
COPY docker/startup.sh /app/startup.sh

# Fix line endings (CRLF to LF) and make executable
RUN sed -i 's/\r$//' /app/startup.sh && chmod +x /app/startup.sh

# Create upload directory
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

EXPOSE 5000

CMD ["/app/startup.sh"]

FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY proxy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY proxy/ ./proxy/
COPY proxy/verticals/ ./proxy/verticals/

WORKDIR /app/proxy

# Start all verticals + proxy
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8787 8801 8802 8803

CMD ["/start.sh"]

FROM python:3.11-slim
WORKDIR /app
COPY proxy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY proxy/ ./proxy/
COPY verticals/ ./verticals/
COPY start.sh .
RUN chmod +x start.sh
EXPOSE 8787 8801 8802 8803 8804
CMD ["bash", "start.sh"]

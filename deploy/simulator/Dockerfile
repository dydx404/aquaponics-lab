FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy simulator package
COPY . .

# Run the simulator
# Broker host and port are passed via environment variables
CMD ["python", "run.py", "--broker", "mosquitto", "--port", "1883"]

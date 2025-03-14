FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set flask app environment variable
ENV FLASK_APP=iss_tracker.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose flask port
EXPOSE 5000

# Run flask application
CMD ["flask", "run"]

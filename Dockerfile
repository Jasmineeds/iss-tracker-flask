FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY iss_tracker.py /app/iss_tracker.py
COPY test_iss_tracker.py /app/test_iss_tracker.py

RUN chmod +rx /app/iss_tracker.py

ENV PATH=/app:$PATH

CMD ["python", "./iss_tracker.py"]

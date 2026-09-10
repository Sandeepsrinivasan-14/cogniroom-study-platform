FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

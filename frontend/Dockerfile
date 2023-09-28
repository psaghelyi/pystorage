FROM python:3.11.5

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        git \
        htop \
        atop \
        liberasurecode-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /frontend

COPY . /frontend/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

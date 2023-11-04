FROM python:3.11.5

ENV PORT=9000

WORKDIR /backend

COPY . /backend/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 9000

CMD uvicorn app:app --host 0.0.0.0 --port $PORT

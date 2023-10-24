FROM python:3.11-alpine

WORKDIR /fdlistener

COPY . .

RUN pip install -r requirements.txt

CMD ["python3","main.py"]

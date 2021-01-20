FROM python:slim-buster

RUN pip install kubernetes

COPY trade_client.py /src/
CMD [ "python", "/src/trade_client.py" ]
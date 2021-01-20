FROM python:slim-buster

RUN pip install kubernetes

COPY recommendstockcronjob.py /src/
CMD [ "python", "/src/recommendstockcronjob.py" ]
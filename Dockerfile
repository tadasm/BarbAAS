FROM python:3.7

WORKDIR /app

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

COPY barbora.py /app/barbora.py
ENTRYPOINT [ "python", "-u" ,"barbora.py" ]

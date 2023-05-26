FROM python:3.10

RUN useradd -ms /bin/bash user

RUN mkdir /app

COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

COPY *.py /app

WORKDIR /app
USER user
ENTRYPOINT [ "./discord_client.py" ]

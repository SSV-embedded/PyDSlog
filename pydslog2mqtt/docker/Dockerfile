FROM python:3.9.2-alpine3.12

WORKDIR /opt/app

COPY app ./

RUN pip install --no-cache-dir -r requirements.txt && \
rm requirements.txt

CMD [ "python", "pydslog2mqtt.py" ]

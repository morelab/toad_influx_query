FROM python:3.8

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./toad_influx_query ./toad_influx_query
COPY ./run.sh ./run.sh

RUN mkdir ./config
VOLUME ./config

CMD ["./run.sh"]

# docker run --network=iotoad_network -v $(pwd)/config:/app/config toad_influx_query
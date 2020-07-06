import senml
from aioinflux import iterpoints
from toad_influx_query import logger

from toad_influx_query.influx import Query
from toad_influx_query import influx


def parse_influx_query(topic, data) -> influx.Query:
    return influx.Query(topic, data)


def influx_response_to_senml(query: Query, response):
    logger.log_info(f"Influx to SenML: {query.db}:{query.measure}:{response}...")
    senml_meaurements = [{"bn": query.measure}]
    for point in iterpoints(response, lambda *x, meta: dict(zip(meta["columns"], x))):
        senml_json = {"t": point["time"]}
        # extract SenML time
        if "time" in point:
            senml_json["t"] = point["time"]
        elif "t" in point:
            senml_json["t"] = point["t"]
        else:
            raise ValueError(f"No time in influx points: {response}")
        # extract SenML value
        if "value" in point:
            senml_json["v"] = point["value"]
        elif "v" in point:
            senml_json["v"] = point["v"]
        elif query.operation:
            senml_json["v"] = point[query.operation.lower()]
        else:
            raise ValueError(f"No value found in influx points: {response}")
        # extract SenML name
        if "id" in point:
            senml_json["n"] = f"/{point['id']}"
        # extract SenML unit
        if "unit" in point:
            senml_json["u"] = point["unit"]
        elif "u" in point:
            senml_json["u"] = point["u"]
        else:
            pass
            # raise ValueError(f"No value in influx points: {response}") ?

        senml_meaurements.append(senml_json)
    logger.log_info_verbose(
        f"Influx to SenML:{senml.SenMLDocument.from_json(senml_meaurements).to_json()}"
    )
    return senml.SenMLDocument.from_json(senml_meaurements).to_json()


def publish_response(mqtt_client, topic, senml_data):
    mqtt_client.publish(topic, {"data": senml_data})


def publish_error_response(mqtt_client, topic, error):
    mqtt_client.publish(topic, {"error": error})

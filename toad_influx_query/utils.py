import senml
from aioinflux import iterpoints


def parse_influx_query(topic, data):
    return 1, 2


def influx_response_to_senml(database, measurement, response):
    senml_meaurements = [{"bn": database}]
    for point in iterpoints(response, lambda *x, meta: dict(zip(meta["columns"], x))):
        senml_json = {"t": point["time"]}
        # extract SenML time
        if "time" in point:
            senml_json["t"] = point["time"]
        elif "t" in point:
            senml_json["t"] = point["time"]
        else:
            raise ValueError(f"No time in influx points: {response}")
        # extract SenML value
        if "value" in point:
            senml_json["v"] = point["value"]
        elif "v" in point:
            senml_json["v"] = point["value"]
        else:
            raise ValueError(f"No value in influx points: {response}")
        # extract SenML name
        if "name" in point:
            senml_json["n"] = f"{measurement}/{point['name']}"
        elif "n" in point:
            senml_json["n"] = f"{measurement}/{point['n']}"
        elif "id" in point:
            senml_json["n"] = f"{measurement}/{point['id']}"
        else:
            senml_json["n"] = measurement
        # extract SenML unit
        if "unit" in point:
            senml_json["u"] = point["unit"]
        elif "u" in point:
            senml_json["u"] = point["u"]
        else:
            pass
            # raise ValueError(f"No value in influx points: {response}") ?

        senml_meaurements.append(senml_json)
    return senml.SenMLDocument.from_json(senml_meaurements).to_json()


def publish_response(mqtt_client, topic, senml_data):
    mqtt_client.publish(topic, {"data": senml_data})


def publish_error_response(mqtt_client, topic, error):
    mqtt_client.publish(topic, {"error": error})

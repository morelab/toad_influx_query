from toad_influx_query.utils import parse_influx_query
import strict_rfc3339


def test_parse_correct_query():
    expected_database = "sp"
    measurement = "energy"
    from_time = 1585217932.2041745
    mqtt_data = {"operation": "sum", "type": "w", "from": str(from_time)}
    expected_query = f'SELECT SUM("value") FROM {measurement} WHERE time >= "{strict_rfc3339.timestamp_to_rfc3339_utcoffset(from_time)}"'
    mqtt_topic = f"query/influx_query/{expected_database}/{measurement}"
    database, query = parse_influx_query(mqtt_topic, mqtt_data)
    assert expected_database == database
    assert expected_query == query

import asyncio

from toad_influx_query import config
from toad_influx_query.mqtt import MQTT
from toad_influx_query import protocol


if __name__ == "__main__":
    mqtt = MQTT("toad_influx_query")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mqtt.run(
        broker_host=config.MQTT_BROKER_HOST,
        message_handler=mqtt.handle_message,
        topics=[protocol.TOPIC]
    ))
    loop.run_forever()

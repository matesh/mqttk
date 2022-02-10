from paho.mqtt.client import MQTTv5, MQTTv31, MQTTv311

COLOURS = ['#9e0505', '#06941b', '#0f05a1', '#999c03', '#048c85', '#5d047a', '#7a3f04',
           '#3b9669', '#b88511', '#1a5e99']

CONNECT = "connected"
DISCONNECT = "disconnected"
QOS_NAMES = {
    "QoS 0": 0,
    "QoS 1": 1,
    "QoS 2": 2
}
DECODER_OPTIONS = [
    "Plain data",
    "JSON pretty formatter",
    "Hex formatter"
]


PROTOCOL_LOOKUP = {
    "3.1": MQTTv31,
    "3.1.1": MQTTv311,
    "5.0": MQTTv5
}

SSL_LIST = ["Disabled", "CA signed server certificate", "CA certificate file", "Self-signed certificate"]

ERROR_CODES = {
    1: "Incorrect protocol version",
    2: "Invalid client identifier",
    3: "Server unavailable",
    4: "Bad username or password",
    5: "Not authorised"
}


MQTT_VERSION_LIST = list(PROTOCOL_LOOKUP.keys())

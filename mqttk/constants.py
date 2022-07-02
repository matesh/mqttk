"""
MQTTk - Lightweight graphical MQTT client and message analyser

Copyright (C) 2022  Máté Szabó

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

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

EVENT_LEVELS = {
    0: "[i]",
    1: "[w]",
    2: "[E]",
    3: "[X]"
}


MQTT_VERSION_LIST = list(PROTOCOL_LOOKUP.keys())

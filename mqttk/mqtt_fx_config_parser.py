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

try:
    import xmltodict
    XMLTODICT = True
except ImportError:
    XMLTODICT = False


def validate(value):
    if value is not None:
        return value
    return ""


def parse_mqttfx_xml(mqttfx_config_file):
    try:
        with open(mqttfx_config_file, 'r') as configfile:
            mqttfx_config_xml = configfile.read()

        mqttfx_config_dict = xmltodict.parse(mqttfx_config_xml)
    except Exception as e:
        return True, "Failed to parse MQTT.fx configuration XML: {}".format(e)
    return False, mqttfx_config_dict


def parse_mqttfx_config(mqttfx_config_dict, mqttk_configuration):

    connection_profiles = mqttfx_config_dict.get("configuration", {}).get(
        "connectionProfiles", {}).get("connectionProfile", None)

    if connection_profiles is None:
        return True, "Unexpected MQTT.fx configuration format"

    if "connections" not in mqttk_configuration:
        mqttk_configuration["connections"] = {}

    for connection_profile in connection_profiles:
        profile_name = "MQTT.fx {}".format(connection_profile["profileName"])
        mqttk_configuration["connections"][profile_name] = {
                "connection_parameters": {},
                "subscriptions": {},
                "publish_topics": [],
                "stored_publishes": {}
            }

        mqttk_configuration["connections"][profile_name]["connection_parameters"]["broker_addr"] = validate(connection_profile["brokerAddress"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["broker_port"] = validate(connection_profile["brokerPort"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["client_id"] = validate(connection_profile["connectionOptions"]["clientId"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["user"] = validate(connection_profile["connectionOptions"]["userName"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["pass"] = validate(connection_profile["connectionOptions"]["password"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["timeout"] = validate(connection_profile["connectionOptions"]["connectionTimeout"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["keepalive"] = validate(connection_profile["connectionOptions"]["keepAliveInterval"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["mqtt_version"] = validate(connection_profile["connectionOptions"]["mqttVersion"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["ssl"] = "Disabled"
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["ca_file"] = validate(connection_profile["connectionOptions"]["caFile"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["cl_cert"] = validate(connection_profile["connectionOptions"]["clientCertificateFile"])
        mqttk_configuration["connections"][profile_name]["connection_parameters"]["cl_key"] = validate(connection_profile["connectionOptions"]["clientKeyFile"])
        # TODO add dialog to check ssl configuration

        if connection_profile["preDefinedMessages"] is not None:
            if type(connection_profile["preDefinedMessages"]["message"]) is list:
                for predefined_message in connection_profile["preDefinedMessages"]["message"]:
                    mqttk_configuration["connections"][profile_name]["stored_publishes"][predefined_message['name']] = {
                        "topic": predefined_message['topic']["name"],
                        "qos": int(predefined_message['qos']),
                        "retained": bool(predefined_message['retained']),
                        "payload": predefined_message['payload']
                    }

        if connection_profile["recentPublishTopics"] is not None:
            if type(connection_profile["recentPublishTopics"]["topic"]) is list:
                for topic in connection_profile["recentPublishTopics"]["topic"]:
                    if "#" in topic or '+' in topic or '%' in topic:
                        continue
                    mqttk_configuration["connections"][profile_name]["publish_topics"].append(topic)

        if connection_profile["recentSubscriptionTopics"] is not None:
            if type(connection_profile["recentSubscriptionTopics"]["topic"]) is list:
                for subscription_topic in connection_profile["recentSubscriptionTopics"]["topic"]:
                    mqttk_configuration["connections"][profile_name]["subscriptions"][subscription_topic["name"]] = {
                        "colour": subscription_topic["color"].lower()
                    }

    return False, mqttk_configuration

import sys
import os
from pathlib import Path
import json

home_dir = str(Path.home())


class ConfigHandler:
    def __init__(self):
        """
        Config handler.
        self.configuration_dict = {
            "connection_profile_name": {
                "connection_parameters": {
                    "connection_parameter: value
                },
                "subscriptions": [] list of previous subscriptions
                "publishes": [] list of previous publishes
                "stored_publishes": [
                    {
                        "topic": topic,
                        "qos": qos,
                        "payload": payload,
                        "retained": retained
                ]
            }
        }

        connection parameters:
        - broker_addr
        - broker_port
        - client_id
        - user
        - pass
        - timeout
        - keepalive
        - mqtt_version
        - ssl
        - ca_file
        - cl_cert
        - cl_key

        """
        self.configuration_dict = {}
        self.wont_save = False
        self.load_config()

    def load_config(self):
        if sys.platform.startswith("win"):
            self.configuration_dict = {}

        elif sys.platform.startswith("linux"):
            self.configuration_dict = {}

        elif sys.platform.startswith("darwin"):
            config_file = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk", "MQTTk-config.json")
            if not os.path.isfile(config_file):
                if not os.path.isdir(os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk")):
                    os.mkdir(os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk"))

                with open(config_file, "w") as configfile:
                    configfile.write("{}")

            with open(config_file, "r") as configfile:
                configuration = configfile.read()

            try:
                self.configuration_dict = json.loads(configuration)
            except Exception as e:
                print("Failed to load config")
        else:
            self.wont_save = True
            raise AssertionError

    def get_connection_profiles(self):
        return list(self.configuration_dict.keys())

    def get_connection_config_dict(self, connection):
        return self.configuration_dict.get(connection, {}).get("connection_parameters", {})

    def save_connection_config(self, connection_name, connection_config):
        print(connection_name, connection_config)
        if connection_name not in self.configuration_dict:
            self.configuration_dict[connection_name] = {
                "connection_parameters": {},
                "subscriptions": [],
                "publishes": [],
                "stored_publishes": []
            }
            self.configuration_dict[connection_name] = connection_config

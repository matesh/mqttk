import sys
import os
from pathlib import Path
import json



LOAD = "load"
SAVE = "save"


class ConfigHandler:
    def __init__(self):
        """
        Config handler.

        configuration_dict = {
            "connections": {}
            "last_used_connection": {}
        }

        configuration_dict[connections] = {
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
        self.config_file_manager(LOAD)
        self.first_start = True

    def config_file_manager(self, action):
        if sys.platform.startswith("win"):
            appdata_dir = os.getenv('LOCALAPPDATA')
            config_dir = os.path.join(appdata_dir, "MQTTk")
            config_file = os.path.join(appdata_dir, "MQTTk", "MQTTk-config.json")

        elif sys.platform.startswith("linux"):
            self.configuration_dict = {}
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, ".config", "MQTTk")
            config_file = os.path.join(home_dir, ".config", "MQTTk", "MQTTk-config.json")

        elif sys.platform.startswith("darwin"):
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk")
            config_file = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk", "MQTTk-config.json")
        else:
            self.wont_save = True
            raise AssertionError

        if not os.path.isfile(config_file):
            self.first_start = True
            if not os.path.isdir(config_dir):
                os.makedirs(config_dir)
            with open(config_file, "w") as configfile:
                configfile.write("{}")

        else:
            if action == LOAD:
                with open(config_file, "r") as configfile:
                    configuration = configfile.read()
                try:
                    self.configuration_dict = json.loads(configuration)
                except Exception as e:
                    print("Failed to load config", e)
            else:
                with open(config_file, "w") as config_file:
                    try:
                        config_string = json.dumps(self.configuration_dict, indent=2)
                    except Exception as e:
                        print("Failed to save configuration", e)
                    else:
                        config_file.write(config_string)

    def get_connection_profiles(self):
        return list(self.configuration_dict.get("connections", {}).keys())

    def get_connection_config_dict(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {})

    def remove_connection_config(self, connection_name):
        self.configuration_dict.get("connections", {}).pop(connection_name, None)
        self.config_file_manager(SAVE)

    def save_connection_config(self, connection_name, connection_config):
        if "connections" not in self.configuration_dict:
            self.configuration_dict["connections"] = {}
        if connection_name not in self.configuration_dict["connections"]:
            self.configuration_dict["connections"][connection_name] = {
                "connection_parameters": {},
                "subscriptions": [],
                "publishes": [],
                "stored_publishes": []
            }
            self.configuration_dict["connections"][connection_name]["connection_parameters"] = connection_config
        self.config_file_manager(SAVE)

    def add_subscription_history(self, connection, topic):
        if topic not in self.configuration_dict[connection]["subscriptions"]:
            self.configuration_dict[connection].append(topic)
        self.config_file_manager(SAVE)

    def get_last_used_connection(self):
        return self.configuration_dict.get("last_used_connection", "")

    def update_last_used_connection(self, connection):
        self.configuration_dict["last_used_connection"] = connection

    def add_publish_history(self, topic):
        pass

    def add_publish_template(self, publish_template):
        pass

    def get_subscription_history(self):
        pass

    def get_publish_history(self):
        pass

    def get_publish_templates(self):
        pass

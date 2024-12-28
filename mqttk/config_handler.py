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

import sys
import os
import traceback
from pathlib import Path
import json
from tkinter import messagebox
from tkinter import filedialog
import mqttk.mqtt_fx_config_parser as configparser
from datetime import datetime

LOAD = "load"
SAVE = "save"

DEFAULT_CONFIGURATION = {
    "connections": {
        "test.mosquitto.org": {
            "connection_parameters": {
            "broker_addr": "test.mosquitto.org",
            "broker_port": "1883",
            "client_id": "272fb6890d1c4eefac4f46b39deb83fb",
            "user": "",
            "pass": "",
            "timeout": "10",
            "keepalive": "60",
            "mqtt_version": "3.1.1",
            "ssl": "Disabled",
            "ca_file": "",
            "cl_cert": "",
            "cl_key": ""
            },
        "subscriptions": {},
        "publish_topics": [],
        "stored_publishes": {},
        "last_subscribe_used": "#"
        }
    }
}


class ConfigHandler:
    def __init__(self, logger):
        """
        Config handler.

        configuration_dict = {
            "connections": {}
            "last_used_connection": connection name,
            "window_geometry: last used window geometry string,
            "autoscroll: true/false,
            "last_used_decoder": last used message decoder,
            "last_used_directory": last used directory for browsing files
        }

        configuration_dict[connections] = {
            "connection_profile_name": {
                "connection_parameters": {
                    "connection_parameter: value
                },
                "subscriptions": { list of previous subscriptions
                    "subscription_topic": {
                        "colour": color
                    }
                }
                "publish_topics": [] list of previous publishes
                "stored_publishes": {
                    "name": {
                        "topic": topic,
                        "qos": qos,
                        "payload": payload,
                        "retained": retained
                },
                "last_publish_used": last publish,
                "last_subscribe_used: last subscribe
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
        self.log_file = None
        self.wont_save = False
        self.first_start = True
        self.log = logger
        self.mqttfx_config_location = None
        self.config_file_manager(LOAD)

    def config_file_manager(self, action):
        if self.wont_save:
            return
        if sys.platform.startswith("win"):
            if self.first_start:
                self.log.info("Windoze platform detected")
                appdata_dir = os.getenv('LOCALAPPDATA')
                mqttfx_config_file = os.path.join(appdata_dir, "MQTT-FX", "mqttfx-config.xml")
                if os.path.isfile(mqttfx_config_file):
                    self.mqttfx_config_location = mqttfx_config_file
                    self.log.info("Found MQTT.fx configuration file", self.mqttfx_config_location)

            appdata_dir = os.getenv('LOCALAPPDATA')
            config_dir = os.path.join(appdata_dir, "MQTTk")
            config_file = os.path.join(appdata_dir, "MQTTk", "MQTTk-config.json")
            self.log_file = os.path.join(appdata_dir, "MQTTk", "MQTTk-log.txt")

        elif sys.platform.startswith("linux"):
            if self.first_start:
                self.log.info("Linux platform detected")
                home_dir = str(Path.home())
                mqttfx_config_file = os.path.join(home_dir, "MQTT-FX", "mqttfx-config.xml")
                if os.path.isfile(mqttfx_config_file):
                    self.mqttfx_config_location = mqttfx_config_file
                    self.log.info("Found MQTT.fx configuration file", self.mqttfx_config_location)

            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, ".config", "MQTTk")
            config_file = os.path.join(home_dir, ".config", "MQTTk", "MQTTk-config.json")
            self.log_file = os.path.join(home_dir, ".config", "MQTTk", "MQTTk-log.txt")

        elif sys.platform.startswith("darwin"):
            if self.first_start:
                self.log.info("MacOS platform detected")
                home_dir = str(Path.home())
                mqttfx_config_file = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTT-FX", "mqttfx-config.xml")
                if os.path.isfile(mqttfx_config_file):
                    self.mqttfx_config_location = mqttfx_config_file
                    self.log.info("Found MQTT.fx configuration file", self.mqttfx_config_location)

            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk")
            config_file = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk", "MQTTk-config.json")
            self.log_file = os.path.join(home_dir, "Library", "ApplicationSupport", "MQTTk", "MQTTk-log.txt")
        else:
            self.log.warning("Unsupported platform detected. Configuration file won't be saved! Use this thing at your own risk :(")
            self.wont_save = True

        self.first_start = False

        if self.wont_save:
            return

        if not os.path.isfile(config_file):
            self.configuration_dict = DEFAULT_CONFIGURATION
            self.first_start = True
            if not os.path.isdir(config_dir):
                os.makedirs(config_dir)
            with open(config_file, "w", encoding="utf-8") as configfile:
                configfile.write(json.dumps(self.configuration_dict, indent=2, ensure_ascii=False))

        else:
            if action == LOAD:
                with open(config_file, "r", encoding="utf-8") as configfile:
                    configuration = configfile.read()
                try:
                    self.configuration_dict = json.loads(configuration)
                except Exception as e:
                    self.log.error("Failed to load config", e)
            else:
                with open(config_file, "w", encoding="utf-8") as config_file:
                    try:
                        config_string = json.dumps(self.configuration_dict, indent=2, ensure_ascii=False)
                    except Exception as e:
                        self.log.error("Failed to save configuration", e)
                    else:
                        config_file.write(config_string)

    def get_connection_profiles(self):
        return list(self.configuration_dict.get("connections", {}).keys())

    def get_connection_config_dict(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {})

    def remove_connection_config(self, connection_name):
        self.configuration_dict.get("connections", {}).pop(connection_name, None)
        self.config_file_manager(SAVE)

    def get_connection_broker_parameters(self, connection):
        return self.configuration_dict["connections"].get(connection, {}).get("connection_parameters", {})

    def save_connection_config(self, connection_name, connection_config):
        if "connections" not in self.configuration_dict:
            self.configuration_dict["connections"] = {}
        if connection_name not in self.configuration_dict["connections"]:
            self.configuration_dict["connections"][connection_name] = {
                "connection_parameters": {},
                "subscriptions": {},
                "publish_topics": [],
                "stored_publishes": {}
            }
        self.configuration_dict["connections"][connection_name]["connection_parameters"] = connection_config
        self.config_file_manager(SAVE)

    def save_connection_dict(self, connection_name, connection_config):
        if "connections" not in self.configuration_dict:
            self.configuration_dict["connections"] = {}
        self.configuration_dict["connections"][connection_name] = connection_config
        self.config_file_manager(SAVE)

    def add_subscription_history(self, connection, topic, colour):
        self.configuration_dict["connections"][connection]["subscriptions"][topic] = {
                "colour": colour
            }
        self.configuration_dict["connections"][connection]["last_subscribe_used"] = topic
        self.config_file_manager(SAVE)

    def get_subscription_history_list(self, connection):
        try:
            return list(self.configuration_dict.get("connections", {}).get(connection, {}).get("subscriptions", {}).keys())
        except AttributeError:
            try:
                self.configuration_dict["connections"][connection]["subscriptions"] = {}
            except Exception:
                self.log.error("Fatal subscription history incompatibility in the config")
            return None

    def get_subscription_colour(self, connection, topic):
        return self.configuration_dict.get("connections", {}).get(
            connection, {}).get("subscriptions", {}).get(topic, {}).get("colour", None)

    def get_window_geometry(self):
        return self.configuration_dict.get("window_geometry", None)

    def save_window_geometry(self, window_geometry):
        self.configuration_dict["window_geometry"] = window_geometry
        self.config_file_manager(SAVE)

    def get_last_used_connection(self):
        return self.configuration_dict.get("last_used_connection", "")

    def update_last_used_connection(self, connection):
        self.configuration_dict["last_used_connection"] = connection

    def get_autoscroll(self):
        return bool(self.configuration_dict.get("autoscroll", False))

    def save_autoscroll(self, value):
        self.configuration_dict["autoscroll"] = bool(value)
        self.config_file_manager(SAVE)

    def get_decompress(self):
        return bool(self.configuration_dict.get("decompress", False))

    def save_decompress(self, value):
        self.configuration_dict["decompress"] = bool(value)
        self.config_file_manager(SAVE)

    def get_decoder(self):
        return self.configuration_dict.get("decoder", "Plain data")

    def save_decoder(self, value):
        self.configuration_dict["decoder"] = value
        self.config_file_manager(SAVE)

    def delete_publish_history_item(self, connection, name):
        try:
            self.configuration_dict["connections"][connection]["stored_publishes"].pop(name, None)
        except Exception as e:
            self.log.warning("Failed to remove history publish item", e, connection, name)

    def get_publish_history(self, connection):
        return self.configuration_dict["connections"].get(connection, {}).get("stored_publishes", {})

    def save_publish_history_item(self, connection, name, config):
        try:
            if "stored_publishes" not in self.configuration_dict["connections"][connection]:
                self.configuration_dict["connections"][connection]["stored_publishes"] = {
                    name: config
                }
            else:
                self.configuration_dict["connections"][connection]["stored_publishes"][name] = config
            self.config_file_manager(SAVE)
        except Exception as e:
            self.log.warning("Exception saving publish history config", e)

    def get_publish_topic_history(self, connection):
        return self.configuration_dict["connections"].get(connection, {}).get("publish_topics", [])

    def save_publish_topic_history_item(self, connection, topic):
        try:
            new = True
            if "publish_topics" not in self.configuration_dict["connections"][connection]:
                self.configuration_dict["connections"][connection]["publish_topics"] = [topic]
            else:
                if topic not in self.configuration_dict["connections"][connection]["publish_topics"]:
                    self.configuration_dict["connections"][connection]["publish_topics"].append(topic)
                else:
                    new = False
            self.configuration_dict["connections"][connection]["last_publish_used"] = topic
            self.config_file_manager(SAVE)
            return new
        except Exception as e:
            self.log.error("Error saving publish topic history item", e)
        self.config_file_manager(SAVE)

    def get_last_publish_topic(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {}).get("last_publish_used", "")

    def get_last_subscribe_used(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {}).get("last_subscribe_used", "")

    def get_last_used_decoder(self):
        return self.configuration_dict.get("last_used_decoder", "None")

    def save_last_used_decoder(self, decoder):
        self.configuration_dict["last_used_decoder"] = decoder
        self.config_file_manager(SAVE)

    def import_mqttfx_config(self):
        if configparser.XMLTODICT is False:
            messagebox.showerror("Error", "Failed to import the xmltodict library. Please ensure all dependencies are installed!")
        if self.mqttfx_config_location is None:
            response = messagebox.askquestion("MQTT.fx config not found", "Couldn't find MQTT.fx configuration file. Would you like to browse the file?")
            if response == "no":
                return False
            mqtt_fx_config_file = filedialog.askopenfilename(initialdir=str(Path.home()),
                                                             title="Select MQTT.fx configuration file")
            if not os.path.isfile(mqtt_fx_config_file):
                messagebox.showerror("Error", "File cannot be found")
                return False
        else:
            mqtt_fx_config_file = self.mqttfx_config_location

        error, response = configparser.parse_mqttfx_xml(mqtt_fx_config_file)
        if error:
            messagebox.showerror("Error", response)
            return False

        error, response = configparser.parse_mqttfx_config(response, self.configuration_dict)
        if error:
            messagebox.showerror("Error", "Failed to parse MQTT.fx config dict: {}".format(response))
            return False

        messagebox.showinfo("Success!", "Successfully imported MQTT.fx configuration! Please double check SSL configuration!")
        self.config_file_manager(SAVE)
        self.configuration_dict = response
        return True

    def get_last_used_directory(self):
        if "last_used_directory" not in self.configuration_dict:
            self.configuration_dict["last_used_directory"] = Path.home()
        if not os.path.isdir(self.configuration_dict["last_used_directory"]):
            self.configuration_dict["last_used_directory"] = Path.home()
        return self.configuration_dict["last_used_directory"]

    def save_last_used_directory(self, directory):
        head, tail = os.path.split(directory)
        self.configuration_dict["last_used_directory"] = head
        self.config_file_manager(SAVE)

    def add_log_message(self, message):
        if self.log_file is not None:
            if not os.path.isfile(self.log_file):
                with open(self.log_file, 'w', encoding="utf-8") as logfile:
                    logfile.write("New log file started {}{}".format(datetime.now().strftime("%Y/%m/%d, %H:%M:%S.%f"),
                                                                     os.linesep))
            with open(self.log_file, 'a', encoding="utf-8") as logfile:
                logfile.write(message)

    def save_export_encode_selection(self, value):
        self.configuration_dict["export_encoding"] = value
        self.config_file_manager(SAVE)

    def get_export_encode_selection(self):
        return self.configuration_dict.get("export_encoding", 1)

    def get_resubscribe(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {}).get("connection_parameters", {}).get("resubscribe", 0)

    def get_resubscribe_topics(self, connection):
        return self.configuration_dict.get("connections", {}).get(connection, {}).get("resubscribe_topics", [])

    def save_resubscribe_topics(self, connection, topics):
        try:
            self.configuration_dict["connections"][connection]["resubscribe_topics"] = topics
            self.config_file_manager(SAVE)
        except Exception as e:
            self.log.error("Failed to save resubscribe topics:", e)
